from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from services.mfcc_service import MFCCService
from services.motor_inferencia import MotorInferencia
from models.conexion_db import db_admin
import shutil
import os
import subprocess
import logging
import tempfile

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
mfcc_service = MFCCService()
motor = MotorInferencia()

# Usar variable de entorno para ffmpeg
FFMPEG_PATH = os.getenv("FFMPEG_PATH", r"C:\ffmpeg\bin\ffmpeg.exe")

class EvaluacionManual(BaseModel):
    id_nino: int
    id_evaluacion: int
    id_hecho: int
    valor: float
def obtener_id_tipo_evidencia(nombre_tipo: str) -> int:
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_tipo FROM tipo_evidencia WHERE nombre = %s",
                (nombre_tipo,)
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Tipo de evidencia '{nombre_tipo}' no existe")
            return result[0]
    except Exception as e:
        logger.error(f"Error obteniendo id_tipo_evidencia para '{nombre_tipo}': {e}")
        raise
@router.post("/iniciar-evaluacion")
async def iniciar_evaluacion(id_nino: int = Form(...)):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO evaluacion_sesion (id_nino, tipo_evaluacion) 
                VALUES (%s, 'Control')
            """
            cursor.execute(query, (id_nino,))
            id_evaluacion = cursor.lastrowid
            conn.commit()
            return {"status": "success", "id_evaluacion": id_evaluacion}
    except Exception as e:
        logger.error(f"Error iniciando evaluación para id_nino={id_nino}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/evaluar-fonema")
async def evaluar_fonema(
    id_nino: int = Form(...),
    id_evaluacion: int = Form(...),
    fonema_objetivo: str = Form(...),
    audio: UploadFile = File(...)
):
    temp_audio_path = None
    try:
        logger.info(f"Recibida petición evaluar_fonema: id_nino={id_nino}, id_evaluacion={id_evaluacion}, fonema_objetivo={fonema_objetivo}, audio.filename={audio.filename}")

        # Validar entrada
        if not fonema_objetivo or not audio.filename:
            raise HTTPException(status_code=400, detail="Parámetros inválidos")

        nombre_fonema = mapear_id_a_nombre(fonema_objetivo)
        # Remover validación estricta del mapeo para permitir fonemas no mapeados

        # Crear directorio temporal si no existe
        temp_dir = "data/temp_audios"
        os.makedirs(temp_dir, exist_ok=True)

        # Usar archivo temporal
        ext = audio.filename.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}", dir=temp_dir) as temp_file:
            temp_audio_path = temp_file.name
            shutil.copyfileobj(audio.file, temp_file)

        audio_path = temp_audio_path

        # Convertir a WAV si es necesario
        if ext in ['webm', 'ogg', 'mp3']:
            wav_path = audio_path.replace(f'.{ext}', '.wav')
            try:
                subprocess.run([
                    FFMPEG_PATH, '-y', '-i', audio_path,
                    '-acodec', 'pcm_s16le', '-ar', '16000', wav_path
                ], check=True, capture_output=True)
                audio_path = wav_path
                os.remove(temp_audio_path)
                temp_audio_path = audio_path  # Actualizar para limpieza
            except subprocess.CalledProcessError as e:
                logger.error(f"Error convirtiendo audio: {e}")
                raise HTTPException(status_code=500, detail="Error procesando el audio")

        # Obtener resultado del MFCC
        porcentaje_similitud = mfcc_service.procesar_evaluacion(
            audio_nino_path=audio_path,
            fonema=nombre_fonema,
            id_ev=id_evaluacion
        )

        # Actualizar rendimiento y memoria de trabajo
        actualizar_rendimiento(id_nino, int(fonema_objetivo), porcentaje_similitud)
        insertar_en_memoria_trabajo(id_evaluacion, fonema_objetivo, porcentaje_similitud, "MFCC", 0.9)

        return {
            "status": "success",
            "similitud_detectada": round(porcentaje_similitud, 4),
            "id_hecho": fonema_objetivo,
            "fonema_evaluado": nombre_fonema
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en evaluar_fonema: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except OSError:
                pass

# CORRECCIÓN: ahora el endpoint de evaluación manual también actualiza el rendimiento histórico y obtiene id_tipo_evidencia dinámicamente para mantener consistencia con el endpoint de evaluación automática 23/04/26
@router.post("/evaluar-manual")
async def evaluar_manual(datos: EvaluacionManual):
    try:
        # Validar entrada
        if not isinstance(datos.valor, (int, float)) or not (0 <= datos.valor <= 1):
            raise HTTPException(status_code=400, detail="Valor debe ser un número entre 0 y 1")

        actualizar_rendimiento(datos.id_nino, datos.id_hecho, datos.valor)
        insertar_en_memoria_trabajo(datos.id_evaluacion, str(datos.id_hecho), datos.valor, "OTRO", 1.0)

        return {"status": "success", "similitud_detectada": datos.valor}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en evaluar_manual: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
# NUEVO ENDPOINT PARA OBTENER PLAN DE EJERCICIOS PERSONALIZADO BASADO EN RENDIMIENTO HISTÓRICO Y HECHOS OBJETIVO DE LOS EJERCICIOS 23/04/26
@router.get("/plan-evaluacion/{id_nino}")
async def obtener_plan_personalizado(id_nino: int):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT 
                e.*,
                COALESCE(rh.promedio, 0) as rendimiento
            FROM catalogo_ejercicios e
            LEFT JOIN rendimiento_hecho rh 
                ON e.id_hecho_objetivo = rh.id_hecho 
                AND rh.id_nino = %s
            ORDER BY
                CASE
                    WHEN rh.promedio IS NULL THEN 1   -- Nunca evaluado (exploración)
                    WHEN rh.promedio < 0.4 THEN 2     -- Débil (zona de desarrollo)
                    WHEN rh.promedio BETWEEN 0.4 AND 0.7 THEN 3 -- Zona óptima ZPD
                    ELSE 4 -- Dominado
                END,
                rh.promedio ASC
            """

            cursor.execute(query, (id_nino,))
            ejercicios = cursor.fetchall()

            return {
                "id_nino": id_nino,
                "plan_adaptativo": ejercicios
            }

    except Exception as e:
        logger.error(f"Error obteniendo plan de evaluación para id_nino={id_nino}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
        
def mapear_id_a_nombre(entrada):
    mapeo_inv = {'1': 'r', '2': 'ere', '3': 's', '4': 'l', '5': 'c', '6': 't', '7': 'd', '8': 'p', '9': 'b', '10': 'g', '14': 'f', '16': 'ch'}
    return mapeo_inv.get(str(entrada), entrada)
# controllers/evaluacion_controller.py

# controllers/evaluacion_controller.py

@router.get("/ejecutar-diagnostico/{id_nino}/{id_evaluacion}")
async def ejecutar_diagnostico(id_nino: int, id_evaluacion: int):
    try:
        # Validar entrada
        if id_nino <= 0 or id_evaluacion <= 0:
            raise HTTPException(status_code=400, detail="IDs inválidos")

        # Usamos el método de tu Motor de Inferencia
        resultados = motor.ejecutar_diagnostico_completo(id_nino, id_evaluacion)
        return {"status": "success", "diagnosticos": resultados}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando diagnóstico para id_nino={id_nino}, id_evaluacion={id_evaluacion}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
# nueva función para actualizar rendimiento después de cada evaluación
def actualizar_rendimiento(id_nino: int, id_hecho: int, nuevo_valor: float):
    try:
        # Validar entrada
        if not isinstance(nuevo_valor, (int, float)) or not (0 <= nuevo_valor <= 1):
            raise ValueError("Valor debe ser un número entre 0 y 1")

        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT promedio, intentos FROM rendimiento_hecho
                WHERE id_nino = %s AND id_hecho = %s
            """, (id_nino, id_hecho))

            row = cursor.fetchone()

            if row:
                promedio_actual = row['promedio']
                intentos = row['intentos'] + 1
                nuevo_promedio = ((promedio_actual * row['intentos']) + nuevo_valor) / intentos

                if nuevo_valor > promedio_actual:
                    tendencia = "Sube"
                elif nuevo_valor < promedio_actual:
                    tendencia = "Baja"
                else:
                    tendencia = "Estable"

                cursor.execute("""
                    UPDATE rendimiento_hecho
                    SET promedio=%s, intentos=%s, tendencia=%s
                    WHERE id_nino=%s AND id_hecho=%s
                """, (nuevo_promedio, intentos, tendencia, id_nino, id_hecho))
            else:
                cursor.execute("""
                    INSERT INTO rendimiento_hecho (id_nino, id_hecho, promedio, intentos, tendencia)
                    VALUES (%s,%s,%s,1,'Estable')
                """, (id_nino, id_hecho, nuevo_valor))

            conn.commit()
    except Exception as e:
        logger.error(f"Error actualizando rendimiento para id_nino={id_nino}, id_hecho={id_hecho}: {e}")
        raise

def insertar_en_memoria_trabajo(id_evaluacion: int, id_hecho: str, valor: float, fuente: str, confiabilidad: float):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            id_tipo = obtener_id_tipo_evidencia(fuente)
            query = """
                INSERT INTO memoria_trabajo 
                (id_ev, id_hecho, valor_obtenido, id_tipo_evidencia, confiabilidad, fuente) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE valor_obtenido = %s
            """
            cursor.execute(query, (
                id_evaluacion, id_hecho, valor, id_tipo, confiabilidad, fuente, valor
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error insertando en memoria_trabajo: {e}")
        raise