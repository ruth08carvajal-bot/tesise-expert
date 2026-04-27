from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.mfcc_service import MFCCService
from services.motor_inferencia import MotorInferencia
from services.explicacion_service import ExplicacionService
from models.conexion_db import db_admin
from controllers.ninos_controller import calcular_edad
import shutil
import os
import subprocess
import logging
import tempfile
import numpy as np
import librosa
from typing import List, Dict  # ← AÑADIR ESTA LÍNEA
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, date

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
mfcc_service = MFCCService()
motor = MotorInferencia()
explicacion_service = ExplicacionService()

# Usar variable de entorno para ffmpeg
#FFMPEG_PATH = os.getenv("FFMPEG_PATH", r"C:\ffmpeg\bin\ffmpeg.exe")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", r"C:\Program Files\GNU Octave\Octave-8.3.0\mingw64\bin\ffmpeg.exe")

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
# inicio de la función para iniciar evaluación con validación de 3 meses entre evaluaciones 26/04/2026
@router.post("/iniciar-evaluacion")
async def iniciar_evaluacion(id_nino: int = Form(...)):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # =========================================================
            # PASO 1: Verificar edad del niño (mínimo 5 años)
            # =========================================================
            cursor.execute("SELECT f_nac, nombre FROM nino WHERE id_nino = %s", (id_nino,))
            nino = cursor.fetchone()
            if not nino:
                raise HTTPException(status_code=404, detail="Niño no encontrado")
            
            edad = calcular_edad(nino['f_nac'])
            
            # 🔴 VALIDACIÓN: Edad mínima 5 años
            if edad < 5:
                return {
                    "status": "error",
                    "puede_evaluar": False,
                    "mensaje": f"El sistema evalúa niños a partir de 5 años. {nino['nombre']} tiene {edad} años."
                }
            
            # =========================================================
            # PASO 2: Verificar si el niño tiene evaluaciones previas
            # =========================================================
            cursor.execute("""
                SELECT id_ev, fecha_eval, tipo_evaluacion 
                FROM evaluacion_sesion 
                WHERE id_nino = %s 
                ORDER BY fecha_eval DESC 
                LIMIT 1
            """, (id_nino,))
            
            ultima_evaluacion = cursor.fetchone()
            
            # =========================================================
            # PASO 3: Si NO tiene evaluaciones previas → crear INICIAL
            # =========================================================
            if not ultima_evaluacion:
                query = """
                    INSERT INTO evaluacion_sesion (id_nino, tipo_evaluacion) 
                    VALUES (%s, 'Inicial')
                """
                cursor.execute(query, (id_nino,))
                id_evaluacion = cursor.lastrowid
                conn.commit()
                return {
                    "status": "success", 
                    "id_evaluacion": id_evaluacion,
                    "tipo": "Inicial",
                    "edad": edad,
                    "mensaje": f"Primera evaluación creada exitosamente para {nino['nombre']} ({edad} años)"
                }
            
            # =========================================================
            # PASO 4: Verificar fecha de última evaluación
            # =========================================================
            fecha_ultima = ultima_evaluacion['fecha_eval']
            
            # Si la fecha es NULL, permitir evaluación
            if fecha_ultima is None:
                query = """
                    INSERT INTO evaluacion_sesion (id_nino, tipo_evaluacion) 
                    VALUES (%s, 'Control')
                """
                cursor.execute(query, (id_nino,))
                id_evaluacion = cursor.lastrowid
                conn.commit()
                return {
                    "status": "success",
                    "id_evaluacion": id_evaluacion,
                    "tipo": "Control",
                    "edad": edad,
                    "mensaje": f"Evaluación creada para {nino['nombre']} ({edad} años)"
                }
            
            # =========================================================
            # PASO 5: Convertir a date si es datetime y calcular meses
            # =========================================================
            hoy = datetime.now().date()
            if isinstance(fecha_ultima, datetime):
                fecha_ultima = fecha_ultima.date()
            
            meses_diferencia = (hoy.year - fecha_ultima.year) * 12 + (hoy.month - fecha_ultima.month)
            
            # =========================================================
            # PASO 6: Si pasaron menos de 3 meses → NO permitir
            # =========================================================
            if meses_diferencia < 3:
                return {
                    "status": "error",
                    "puede_evaluar": False,
                    "id_evaluacion_existente": ultima_evaluacion['id_ev'],
                    "fecha_ultima_evaluacion": fecha_ultima.strftime('%Y-%m-%d'),
                    "meses_restantes": 3 - meses_diferencia,
                    "edad": edad,
                    "mensaje": f"{nino['nombre']} fue evaluado hace {meses_diferencia} meses. Deben pasar al menos 3 meses para una reevaluación."
                }
            
            # =========================================================
            # PASO 7: Si pasaron 3 meses o más → crear reevaluación (CONTROL)
            # =========================================================
            query = """
                INSERT INTO evaluacion_sesion (id_nino, tipo_evaluacion) 
                VALUES (%s, 'Control')
            """
            cursor.execute(query, (id_nino,))
            id_evaluacion = cursor.lastrowid
            conn.commit()
            
            return {
                "status": "success", 
                "id_evaluacion": id_evaluacion,
                "tipo": "Control",
                "edad": edad,
                "fecha_ultima_evaluacion": fecha_ultima.strftime('%Y-%m-%d'),
                "meses_desde_ultima": meses_diferencia,
                "mensaje": f"Reevaluación creada para {nino['nombre']} después de {meses_diferencia} meses"
            }
            
    except Exception as e:
        logger.error(f"Error iniciando evaluación para id_nino={id_nino}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
# fin de la función para iniciar evaluación con validación de 3 meses entre evaluaciones 26/04/2026
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

        # Obtener edad para ajustar MFCC
        edad = obtener_edad_nino(id_nino)

        # Obtener resultado del MFCC
        porcentaje_similitud = mfcc_service.procesar_evaluacion(
            audio_nino_path=audio_path,
            fonema=nombre_fonema,
            id_ev=id_evaluacion,
            edad=edad
        )

        # Actualizar rendimiento y memoria de trabajo
        confiabilidad = obtener_confiabilidad_por_edad(id_nino)
        actualizar_rendimiento(id_nino, int(fonema_objetivo), porcentaje_similitud)
        insertar_en_memoria_trabajo(id_evaluacion, fonema_objetivo, porcentaje_similitud, "MFCC", confiabilidad)

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

def obtener_hechos_relevantes_nino(id_nino: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id_hecho FROM anamnesis_hechos WHERE id_nino = %s
            UNION
            SELECT id_hecho FROM rendimiento_hecho WHERE id_nino = %s AND promedio < 0.4
        """
        cursor.execute(query, (id_nino, id_nino))
        return [row['id_hecho'] for row in cursor.fetchall()]

def obtener_edad_nino(id_nino: int) -> int:
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT f_nac FROM nino WHERE id_nino = %s", (id_nino,))
        row = cursor.fetchone()
        if not row or not row.get('f_nac'):
            raise ValueError(f"Niño con id_nino={id_nino} no encontrado o sin fecha de nacimiento")
        return calcular_edad(row['f_nac'])

#modificar edad para calcular alpha 23/04/2026
def niveles_permitidos_por_edad(edad: int):
    if edad < 6:
        return ['Bajo'] # 5 años: solo ejercicios básicos
    if edad < 8:         
        return ['Bajo', 'Medio']    # 6-7 años: solo ejercicios básicos
    return ['Bajo', 'Medio', 'Alto']    # 8-10 años: solo ejercicios básicos


def obtener_ejercicios_recomendados_por_reglas(id_nino: int, niveles_permitidos=None):
    hechos = obtener_hechos_relevantes_nino(id_nino)
    if not hechos:
        return []

    hechos_unicos = list(dict.fromkeys(hechos))
    placeholders = ','.join(['%s'] * len(hechos_unicos))

    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        query = f"""
            SELECT e.*, COUNT(*) AS soporte
            FROM base_reglas br
            JOIN catalogo_ejercicios e ON br.id_ejercicio_sugerido = e.id_ejercicio
            WHERE br.id_ejercicio_sugerido IS NOT NULL
              AND br.id_hecho IN ({placeholders})
        """
        params = hechos_unicos
        if niveles_permitidos:
            niveles_placeholders = ','.join(['%s'] * len(niveles_permitidos))
            query += f" AND e.nivel_dificultad IN ({niveles_placeholders})"
            params += niveles_permitidos
        query += """
            GROUP BY e.id_ejercicio
            ORDER BY soporte DESC, e.nivel_dificultad ASC
        """
        cursor.execute(query, params)
        ejercicios = cursor.fetchall()
        return ejercicios

@router.get("/plan-evaluacion/{id_nino}")
async def obtener_plan_personalizado(id_nino: int):
    try:
        return construir_plan_personalizado(id_nino)
    except Exception as e:
        logger.error(f"Error obteniendo plan de evaluación para id_nino={id_nino}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
        
def obtener_confiabilidad_por_edad(id_nino: int) -> float:
    try:
        edad = obtener_edad_nino(id_nino)
        if edad < 4:
            return 0.7
        if edad < 6:
            return 0.8
        if edad < 9:
            return 0.9
        return 0.95
    except Exception:
        return 0.9


def mapear_id_a_nombre(entrada):
    mapeo_inv = {'1': 'r', '2': 'ere', '3': 's', '4': 'l', '5': 'c', '6': 't', '7': 'd', '8': 'p', '9': 'b', '10': 'g', '14': 'f', '16': 'ch'}
    return mapeo_inv.get(str(entrada), entrada)
# controllers/evaluacion_controller.py

# controllers/evaluacion_controller.py

@router.get("/ejecutar-diagnostico/{id_nino}/{id_evaluacion}")
async def ejecutar_diagnostico(id_nino: int, id_evaluacion: int):
    try:
        if id_nino <= 0 or id_evaluacion <= 0:
            raise HTTPException(status_code=400, detail="IDs inválidos")

        informe = obtener_informe_clinico(id_nino, id_evaluacion)
        
        # inicio NUEVO: Guardar el diagnóstico en evaluacion_sesion 26/04/2026
        try:
            with db_admin.obtener_conexion() as conn:
                cursor = conn.cursor()
                
                # Generar texto resumen del diagnóstico
                diagnosticos_texto = ""
                for d in informe.get('diagnosticos', []):
                    if d.get('fc_total', 0) > 0.5:
                        diagnosticos_texto += f"- {d.get('nombre_diag', '')} (certeza: {d.get('fc_total', 0)*100:.1f}%)\n"
                
                if not diagnosticos_texto:
                    diagnosticos_texto = "No se encontraron diagnósticos con certeza suficiente (>50%)"
                
                # Generar sugerencia de ejercicios
                ejercicios_texto = ""
                for e in informe.get('plan', [])[:5]:
                    ejercicios_texto += f"- {e.get('nombre_ejercicio', '')} (Nivel: {e.get('nivel_dificultad', '')})\n"
                
                if not ejercicios_texto:
                    ejercicios_texto = "Completar más evaluaciones para obtener recomendaciones personalizadas"
                
                # Actualizar la sesión de evaluación
                query = """
                    UPDATE evaluacion_sesion 
                    SET diagnostico_sistema = %s,
                        pronostico_sistema = %s,
                        sugerencia_ejercicios = %s,
                        explicacion_logica = %s
                    WHERE id_ev = %s
                """
                
                pronostico = _generar_pronostico(informe.get('diagnosticos', []))
                explicacion = informe.get('explicacion_general', 'Evaluación completada. Revise los detalles para más información.')
                
                cursor.execute(query, (
                    diagnosticos_texto,
                    pronostico,
                    ejercicios_texto,
                    explicacion,
                    id_evaluacion
                ))
                conn.commit()
                logger.info(f"Evaluación {id_evaluacion} actualizada con diagnóstico")
                
        except Exception as e:
            logger.error(f"Error guardando diagnóstico en evaluacion_sesion: {e}")
            # No lanzamos excepción para no romper la respuesta al frontend fin NUEVO 26/04/2026
        return {"status": "success", **informe}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando diagnóstico para id_nino={id_nino}, id_evaluacion={id_evaluacion}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
# inicio función para generar pronóstico basado en diagnósticos 26/04/2026
def _generar_pronostico(diagnosticos: List[Dict]) -> str:
    """Genera un pronóstico basado en los diagnósticos encontrados."""
    if not diagnosticos:
        return "Sin diagnósticos concluyentes. Se recomienda seguimiento en 6 meses."
    
    diagnosticos_fuertes = [d for d in diagnosticos if d.get('fc_total', 0) > 0.7]
    diagnosticos_moderados = [d for d in diagnosticos if 0.5 <= d.get('fc_total', 0) <= 0.7]
    
    if diagnosticos_fuertes:
        return """Pronóstico: Reservado a favorable con intervención temprana.
Se recomienda iniciar terapia fonoaudiológica de forma regular (2-3 veces por semana).
Reevaluar en 3 meses para ajustar objetivos terapéuticos."""
    
    elif diagnosticos_moderados:
        return """Pronóstico: Favorable con seguimiento.
Se recomienda implementar ejercicios en casa y seguimiento mensual.
Reevaluar en 6 meses para verificar progresos."""
    
    else:
        return """Pronóstico: Bueno.
El niño se encuentra dentro de parámetros esperados para su edad.
Mantener estimulación en casa y reevaluar anualmente."""
# fin función para generar pronóstico basado en diagnósticos 26/04/2026

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

#endpoint para que el tutor agregue notas inicio 26/04/2026
@router.post("/agregar-notas")
async def agregar_notas_evaluacion(
    id_evaluacion: int = Form(...),
    notas: str = Form(...)
):
    """Permite al tutor agregar notas a una evaluación existente."""
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
                UPDATE evaluacion_sesion 
                SET notas_tutor = %s
                WHERE id_ev = %s
            """
            cursor.execute(query, (notas, id_evaluacion))
            conn.commit()
            
            return {"status": "success", "mensaje": "Notas guardadas correctamente"}
            
    except Exception as e:
        logger.error(f"Error guardando notas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    # fin endpoint para que el tutor agregue notas 26/04/2026
    
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


def obtener_anamnesis_resumen(id_nino: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT bh.id_hecho, bh.descripcion
            FROM anamnesis_hechos ah
            JOIN base_hechos bh ON ah.id_hecho = bh.id_hecho
            WHERE ah.id_nino = %s
        """, (id_nino,))
        return cursor.fetchall()


def obtener_mfcc_scores(id_evaluacion: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT mt.id_hecho, bh.descripcion, mt.valor_obtenido AS score, mt.confiabilidad, mt.fuente
            FROM memoria_trabajo mt
            LEFT JOIN base_hechos bh ON mt.id_hecho = bh.id_hecho
            WHERE mt.id_ev = %s AND mt.fuente = 'MFCC'
        """, (id_evaluacion,))
        return cursor.fetchall()


def construir_plan_personalizado(id_nino: int):
    edad = obtener_edad_nino(id_nino)
    niveles_permitidos = niveles_permitidos_por_edad(edad)
    ejercicios_recomendados = obtener_ejercicios_recomendados_por_reglas(id_nino, niveles_permitidos)

    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        if ejercicios_recomendados:
            excluidos = [str(e['id_ejercicio']) for e in ejercicios_recomendados]
            placeholders = ','.join(['%s'] * len(excluidos))
            niveles_placeholders = ','.join(['%s'] * len(niveles_permitidos))
            query = f"""
                SELECT 
                    e.*, 
                    COALESCE(rh.promedio, 0) as rendimiento
                FROM catalogo_ejercicios e
                LEFT JOIN rendimiento_hecho rh 
                    ON e.id_hecho_objetivo = rh.id_hecho 
                    AND rh.id_nino = %s
                WHERE e.id_ejercicio NOT IN ({placeholders})
                  AND e.nivel_dificultad IN ({niveles_placeholders})
                ORDER BY
                    CASE
                        WHEN rh.promedio IS NULL THEN 1
                        WHEN rh.promedio < 0.4 THEN 2
                        WHEN rh.promedio BETWEEN 0.4 AND 0.7 THEN 3
                        ELSE 4
                    END,
                    rh.promedio ASC
            """
            cursor.execute(query, [id_nino] + excluidos + niveles_permitidos)
            otros_ejercicios = cursor.fetchall()
            plan = ejercicios_recomendados + otros_ejercicios
            fuente = 'reglas_clinicas'
        else:
            niveles_placeholders = ','.join(['%s'] * len(niveles_permitidos))
            query = f"""
                SELECT 
                    e.*, 
                    COALESCE(rh.promedio, 0) as rendimiento
                FROM catalogo_ejercicios e
                LEFT JOIN rendimiento_hecho rh 
                    ON e.id_hecho_objetivo = rh.id_hecho 
                    AND rh.id_nino = %s
                WHERE e.nivel_dificultad IN ({niveles_placeholders})
                ORDER BY
                    CASE
                        WHEN rh.promedio IS NULL THEN 1
                        WHEN rh.promedio < 0.4 THEN 2
                        WHEN rh.promedio BETWEEN 0.4 AND 0.7 THEN 3
                        ELSE 4
                    END,
                    rh.promedio ASC
            """
            cursor.execute(query, [id_nino] + niveles_permitidos)
            plan = cursor.fetchall()
            fuente = 'rendimiento'

    return {
        'id_nino': id_nino,
        'edad_nino': edad,
        'niveles_permitidos': niveles_permitidos,
        'plan_adaptativo': plan,
        'fuente': fuente
    }


def construir_progreso_evaluacion(id_nino: int, id_evaluacion: int, plan: list):
    mfcc_scores = obtener_mfcc_scores(id_evaluacion)
    completados = len(mfcc_scores)
    total_plan = len(plan)
    porcentaje = round((completados / total_plan) * 100, 1) if total_plan else 0
    return {
        'ejercicios_completados': completados,
        'ejercicios_recomendados': total_plan,
        'porcentaje': porcentaje
    }


def obtener_informe_clinico(id_nino: int, id_evaluacion: int):
    edad = obtener_edad_nino(id_nino)
    resultados = motor.ejecutar_diagnostico_completo(id_nino, id_evaluacion, edad)
    # inicio NUEVO: Construir lista de diagnósticos con trazabilidad completa para la explicación 26/04/2026
    diagnosticos_dict = []
    for r in resultados:
        diag_dict = {
            "id_diag": r.id_diag,
            "nombre_diag": r.nombre_diag,
            "fc_total": r.fc_total,
            "explicacion": r.explicacion,
            "hechos_disparadores": r.hechos_disparadores,
            "reglas_aplicadas": r.reglas_aplicadas,
            "confiabilidad": r.confiabilidad,
            "pasos_razonamiento": r.pasos_razonamiento  # NUEVO: trazabilidad completa
        }
        diagnosticos_dict.append(diag_dict)
    # fin NUEVO 26/04/2026
    plan_info = construir_plan_personalizado(id_nino)
    anamnesis = obtener_anamnesis_resumen(id_nino)
    mfcc_scores = obtener_mfcc_scores(id_evaluacion)
    explicacion_general = explicacion_service.generar_resumen_general(
        [r.__dict__ for r in resultados],
        plan_info['plan_adaptativo'],
        anamnesis,
        mfcc_scores
    )

    return {
        'diagnosticos': [r.__dict__ for r in resultados],
        'plan': plan_info['plan_adaptativo'],
        'explicacion_general': explicacion_general,
        'anamnesis': anamnesis,
        'mfcc_scores': mfcc_scores,
        'progreso': construir_progreso_evaluacion(id_nino, id_evaluacion, plan_info['plan_adaptativo']),
        'faq': explicacion_service.preguntas_frecuentes()
    }

#inicio nuevo endpoint para generar PDF clínico completo 26/04/2026
def generar_pdf_clinico(id_nino: int, id_evaluacion: int) -> str:
    """Genera un PDF profesional con el informe clínico completo."""
    
    # Obtener datos actualizados de la BD (incluye lo que guardamos en Paso 1)
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos del niño
        cursor.execute("""
            SELECT n.nombre, n.f_nac, n.genero, n.escolaridad, t.nombre as tutor_nombre
            FROM nino n
            JOIN tutor t ON n.id_tut = t.id_tut
            WHERE n.id_nino = %s
        """, (id_nino,))
        nino = cursor.fetchone()
        
        # Obtener datos de la evaluación (ya actualizados)
        cursor.execute("""
            SELECT diagnostico_sistema, pronostico_sistema, sugerencia_ejercicios, 
                   explicacion_logica, fecha_eval, tipo_evaluacion
            FROM evaluacion_sesion
            WHERE id_ev = %s
        """, (id_evaluacion,))
        evaluacion = cursor.fetchone()
        
        # Obtener puntajes MFCC
        cursor.execute("""
            SELECT bh.descripcion, mt.valor_obtenido, mt.confiabilidad
            FROM memoria_trabajo mt
            JOIN base_hechos bh ON mt.id_hecho = bh.id_hecho
            WHERE mt.id_ev = %s AND mt.fuente = 'MFCC'
            ORDER BY mt.valor_obtenido ASC
        """, (id_evaluacion,))
        mfcc_scores = cursor.fetchall()
        
        # Obtener anamnesis relevante
        cursor.execute("""
            SELECT bh.descripcion
            FROM anamnesis_hechos ah
            JOIN base_hechos bh ON ah.id_hecho = bh.id_hecho
            WHERE ah.id_nino = %s
            LIMIT 10
        """, (id_nino,))
        anamnesis = cursor.fetchall()
    
    # Calcular edad
    edad_nino = calcular_edad(nino['f_nac'])
    
    # Crear PDF
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, f"reporte_clinico_{id_nino}_{id_evaluacion}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y = height - 60
    
    # =========================================================
    # ENCABEZADO
    # =========================================================
    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.2, 0.3, 0.5)  # Color azul institucional
    c.drawString(50, y, "INFORME DE EVALUACIÓN FONOAUDIOLÓGICA")
    y -= 25
    
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, y, f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y')}")
    y -= 20
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "DATOS DEL PACIENTE")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Nombre: {nino['nombre']}")
    y -= 14
    c.drawString(50, y, f"Edad: {edad_nino} años")
    y -= 14
    c.drawString(50, y, f"Género: {nino['genero']}")
    y -= 14
    c.drawString(50, y, f"Escolaridad: {nino['escolaridad']}")
    y -= 14
    c.drawString(50, y, f"Tutor: {nino['tutor_nombre']}")
    y -= 20
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "DATOS DE LA EVALUACIÓN")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Fecha de evaluación: {evaluacion['fecha_eval'].strftime('%d/%m/%Y')}")
    y -= 14
    
    tipo_texto = "Evaluación Inicial" if evaluacion['tipo_evaluacion'] == 'Inicial' else "Evaluación de Control / Reevaluación"
    c.drawString(50, y, f"Tipo: {tipo_texto}")
    y -= 20
    
    # =========================================================
    # DIAGNÓSTICO (desde la BD)
    # =========================================================
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.8, 0.2, 0.2)
    c.drawString(50, y, "DIAGNÓSTICO CLÍNICO")
    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    
    diagnostico_texto = evaluacion.get('diagnostico_sistema', 'No disponible')
    for line in _formatear_parrafo_pdf(diagnostico_texto, 80):
        c.drawString(60, y, line)
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
    y -= 10
    
    # =========================================================
    # PRONÓSTICO (desde la BD)
    # =========================================================
    if y < 120:
        c.showPage()
        y = height - 60
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.2, 0.6, 0.2)
    c.drawString(50, y, "PRONÓSTICO")
    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    
    pronostico_texto = evaluacion.get('pronostico_sistema', 'No disponible')
    for line in _formatear_parrafo_pdf(pronostico_texto, 80):
        c.drawString(60, y, line)
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
    y -= 15
    
    # =========================================================
    # PLAN DE INTERVENCIÓN (desde la BD)
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 60
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.2, 0.3, 0.5)
    c.drawString(50, y, "PLAN DE INTERVENCIÓN / EJERCICIOS RECOMENDADOS")
    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    
    ejercicios_texto = evaluacion.get('sugerencia_ejercicios', 'No disponible')
    for line in _formatear_parrafo_pdf(ejercicios_texto, 80):
        c.drawString(60, y, line)
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
    y -= 15
    
    # =========================================================
    # PUNTAJES MFCC (Rendimiento por fonema)
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 60
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "RENDIMIENTO POR FONEMA (Análisis Acústico MFCC)")
    y -= 18
    c.setFont("Helvetica", 9)
    
    # Cabecera de la tabla
    c.drawString(50, y, "Fonema")
    c.drawString(180, y, "Puntaje")
    c.drawString(280, y, "Interpretación")
    y -= 12
    
    for score in mfcc_scores[:15]:
        valor = score['valor_obtenido']
        descripcion = score['descripcion'][:30] if score['descripcion'] else "Fonema"
        
        if valor >= 0.7:
            interpretacion = "✅ Correcto"
        elif valor >= 0.4:
            interpretacion = "⚠️ En desarrollo"
        else:
            interpretacion = "🔴 Requiere refuerzo"
        
        c.drawString(50, y, descripcion)
        c.drawString(180, y, f"{valor*100:.1f}%")
        c.drawString(280, y, interpretacion)
        y -= 12
        
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 9)
            c.drawString(50, y, "Fonema")
            c.drawString(180, y, "Puntaje")
            c.drawString(280, y, "Interpretación")
            y -= 12
    
    y -= 15
    
    # =========================================================
    # RECOMENDACIONES PARA EL TUTOR
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 60
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "RECOMENDACIONES PARA EL TUTOR")
    y -= 18
    c.setFont("Helvetica", 10)
    
    recomendaciones = [
        "1. Realizar los ejercicios recomendados en casa con una frecuencia de 3-4 veces por semana.",
        "2. Mantener un ambiente tranquilo y sin distracciones durante las sesiones de práctica.",
        "3. Celebrar los logros del niño, incluso los pequeños avances.",
        "4. Consultar con un especialista si persisten las dificultades después de 3 meses de práctica.",
        "5. Utilizar el chatbot 'Asistente Clínico' para resolver dudas sobre los resultados."
    ]
    
    for rec in recomendaciones:
        for line in _formatear_parrafo_pdf(rec, 85):
            c.drawString(60, y, line)
            y -= 12
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 10)
        y -= 4
    
    # =========================================================
    # PIE DE PÁGINA
    # =========================================================
    c.showPage()
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 50, "Documento generado automáticamente por el Sistema Experto Fonoaudiológico")
    c.drawString(50, 40, "Este informe no sustituye la consulta con un especialista.")
    c.drawString(50, 30, f"Reporte ID: {id_evaluacion} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.save()
    return pdf_path


def _formatear_parrafo_pdf(texto: str, ancho: int = 80) -> list:
    """Formatea un texto largo en líneas de máximo 'ancho' caracteres para PDF."""
    if not texto:
        return ["No disponible"]
    
    palabras = texto.split()
    lineas = []
    linea_actual = ""
    
    for palabra in palabras:
        if len(linea_actual) + len(palabra) + 1 <= ancho:
            if linea_actual:
                linea_actual += " " + palabra
            else:
                linea_actual = palabra
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = palabra
    
    if linea_actual:
        lineas.append(linea_actual)
    
    return lineas


@router.get("/generar-reporte-pdf/{id_nino}/{id_evaluacion}")
async def generar_reporte_pdf(id_nino: int, id_evaluacion: int):
    try:
        if id_nino <= 0 or id_evaluacion <= 0:
            raise HTTPException(status_code=400, detail="IDs inválidos")

        pdf_path = generar_pdf_clinico(id_nino, id_evaluacion)
        return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando reporte PDF para id_nino={id_nino}, id_evaluacion={id_evaluacion}: {e}")
        raise HTTPException(status_code=500, detail="No se pudo generar el reporte PDF")
# fin nuevo endpoint para generar PDF clínico completo 26/04/2026
# inicio nuevo endpoint para obtener historial de evaluaciones y rendimiento histórico 26/04/2026
@router.get("/historial-evaluaciones/{id_nino}")
async def obtener_historial_evaluaciones(id_nino: int):
    """Obtiene el historial de evaluaciones de un niño para gráficos de progreso."""
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener todas las evaluaciones del niño
            cursor.execute("""
                SELECT id_ev, fecha_eval, tipo_evaluacion,
                       DATE_FORMAT(fecha_eval, '%d/%m/%Y') as fecha_formateada
                FROM evaluacion_sesion
                WHERE id_nino = %s
                ORDER BY fecha_eval ASC
            """, (id_nino,))
            evaluaciones = cursor.fetchall()
            
            # Para cada evaluación, calcular puntaje promedio de MFCC
            for ev in evaluaciones:
                cursor.execute("""
                    SELECT AVG(valor_obtenido) as promedio
                    FROM memoria_trabajo
                    WHERE id_ev = %s AND fuente = 'MFCC'
                """, (ev['id_ev'],))
                resultado = cursor.fetchone()
                ev['puntaje_promedio'] = float(resultado['promedio']) if resultado and resultado['promedio'] else 0
            
            # Obtener mejores y peores fonemas (promedio histórico)
            cursor.execute("""
                SELECT bh.descripcion, rh.promedio
                FROM rendimiento_hecho rh
                JOIN base_hechos bh ON rh.id_hecho = bh.id_hecho
                WHERE rh.id_nino = %s AND rh.promedio IS NOT NULL
                ORDER BY rh.promedio DESC
            """, (id_nino,))
            rendimientos = cursor.fetchall()
            
            mejores_fonemas = rendimientos[:5]  # Top 5
            peores_fonemas = rendimientos[-5:] if len(rendimientos) >= 5 else []  # Bottom 5
            peores_fonemas = [p for p in peores_fonemas if p['promedio'] < 0.6]
            
            return {
                "status": "success",
                "evaluaciones": evaluaciones,
                "mejores_fonemas": mejores_fonemas,
                "peores_fonemas": peores_fonemas
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo historial para niño {id_nino}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# fin nuevo endpoint para obtener historial de evaluaciones y rendimiento histórico 26/04/2026