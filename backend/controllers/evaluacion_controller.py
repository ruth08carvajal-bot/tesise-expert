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
FFMPEG_PATH = os.getenv("FFMPEG_PATH", r"C:\ffmpeg\bin\ffmpeg.exe")
#FFMPEG_PATH = os.getenv("FFMPEG_PATH", r"C:\Program Files\GNU Octave\Octave-8.3.0\mingw64\bin\ffmpeg.exe")

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
            # PASO 4: Verificar si la última evaluación tiene diagnóstico
            # (Si está incompleta, permitir nueva evaluación)
            # =========================================================
            cursor.execute("""
                SELECT diagnostico_sistema FROM evaluacion_sesion 
                WHERE id_ev = %s
            """, (ultima_evaluacion['id_ev'],))
            
            resultado_diagnostico = cursor.fetchone()
            tiene_diagnostico = resultado_diagnostico and resultado_diagnostico.get('diagnostico_sistema')
            
            # Si la evaluación está incompleta (sin diagnóstico), permitir nueva
            if not tiene_diagnostico:
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
                    "mensaje": f"Nueva evaluación creada (la anterior no se completó)"
                }
            
            # =========================================================
            # PASO 5: Verificar fecha de última evaluación completa
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
            # PASO 6: Convertir a date si es datetime y calcular meses
            # =========================================================
            hoy = datetime.now().date()
            if isinstance(fecha_ultima, datetime):
                fecha_ultima = fecha_ultima.date()
            
            meses_diferencia = (hoy.year - fecha_ultima.year) * 12 + (hoy.month - fecha_ultima.month)
            
            # =========================================================
            # PASO 7: Si pasaron menos de 3 meses → NO permitir
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
            # PASO 8: Si pasaron 3 meses o más → crear reevaluación (CONTROL)
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

#inicio nuevo endpoint para generar PDF clínico completo 27/04/2026 - VERSIÓN CORREGIDA
def generar_pdf_clinico(id_nino: int, id_evaluacion: int) -> str:
    """Genera un PDF profesional con el informe clínico completo - Versión con tablas y pie de página correcto."""
    
    # Obtener datos actualizados de la BD
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos del niño (SOLO columnas que existen)
        cursor.execute("""
            SELECT n.nombre, n.f_nac, n.genero, n.escolaridad, n.parentesco,
                   t.nombre as tutor_nombre, t.celular as tutor_celular, t.email as tutor_email, t.zona as tutor_zona
            FROM nino n
            JOIN tutor t ON n.id_tut = t.id_tut
            WHERE n.id_nino = %s
        """, (id_nino,))
        nino = cursor.fetchone()
        
        if nino is None:
            raise ValueError(f"No se encontró el niño con id {id_nino}")
        
        # Obtener datos de la evaluación
        cursor.execute("""
            SELECT diagnostico_sistema, pronostico_sistema, sugerencia_ejercicios, 
                   explicacion_logica, fecha_eval, tipo_evaluacion, notas_tutor
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
        
        # Obtener anamnesis (con descripciones más limpias)
        cursor.execute("""
            SELECT bh.descripcion
            FROM anamnesis_hechos ah
            JOIN base_hechos bh ON ah.id_hecho = bh.id_hecho
            WHERE ah.id_nino = %s
            ORDER BY ah.id_ana_h ASC
            LIMIT 8
        """, (id_nino,))
        anamnesis = cursor.fetchall()
    
    # Calcular edad exacta
    edad_nino = calcular_edad_exacta(nino['f_nac'])
    fecha_actual = datetime.now()
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, f"informe_clinico_{id_nino}_{id_evaluacion}.pdf")
    
    # Configurar el canvas
    c = canvas.Canvas(pdf_path, pagesize=letter, encoding='utf-8')
    width, height = letter
    y = height - 50
    
    # =========================================================
    # ENCABEZADO PROFESIONAL
    # =========================================================
    # Barra superior decorativa
    c.setFillColorRGB(0.0, 0.4, 0.6)
    c.rect(0, height-40, width, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-28, "SISTEMA EXPERTO DE FONOAUDIOLOGÍA CLÍNICA - BOLIVIA")
    c.setFont("Helvetica", 8)
    c.drawString(50, height-16, "Unidad de Evaluación y Diagnóstico del Lenguaje")
    
    # Línea decorativa
    y = height - 55
    c.setStrokeColorRGB(0.0, 0.4, 0.6)
    c.setLineWidth(2)
    c.line(45, y, width-45, y)
    y -= 18
    
    # Título principal
    c.setFillColorRGB(0.1, 0.2, 0.3)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "INFORME DE EVALUACIÓN FONOAUDIOLÓGICA")
    y -= 22
    
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(50, y, f"Fecha de emisión: {fecha_actual.strftime('%d/%m/%Y')} - {fecha_actual.strftime('%H:%M')} hrs")
    y -= 30
    
    # =========================================================
    # SECCIÓN 1: DATOS DEL PACIENTE
    # =========================================================
    datos_paciente = [
        ("Nombre completo:", nino['nombre']),
        ("Fecha de nacimiento:", nino['f_nac'].strftime('%d/%m/%Y')),
        ("Edad:", edad_nino),
        ("Género:", "Masculino" if nino['genero'] == 'M' else "Femenino"),
        ("Escolaridad:", nino['escolaridad'] or 'No registrada'),
        ("Parentesco con tutor:", nino['parentesco'] or 'No registrado'),
        ("Tutor/a responsable:", nino['tutor_nombre'].title() if nino['tutor_nombre'] else 'No registrado'),
        ("Teléfono de contacto:", nino['tutor_celular'] or 'No registrado'),
        ("Zona de residencia:", nino['tutor_zona'] or 'No registrada')
    ]
    
    y = dibujar_seccion_con_tabla(c, y, "1. DATOS DEL PACIENTE", datos_paciente)
    y -= 10
    
    # =========================================================
    # SECCIÓN 2: DATOS DE LA EVALUACIÓN
    # =========================================================
    if y < 200:
        c.showPage()
        y = height - 50
        dibujar_encabezado_pagina(c, height)
    
    datos_evaluacion = [
        ("Fecha de evaluación:", evaluacion['fecha_eval'].strftime('%d/%m/%Y')),
        ("Tipo de evaluación:", "Evaluación Inicial" if evaluacion['tipo_evaluacion'] == 'Inicial' else "Evaluación de Control"),
        ("Método de evaluación:", "Evaluación Acústica Automatizada (MFCC) + Anamnesis Clínica")
    ]
    
    if evaluacion.get('notas_tutor'):
        datos_evaluacion.append(("Notas del tutor:", evaluacion['notas_tutor'][:60]))
    
    y = dibujar_seccion_con_tabla(c, y, "2. DATOS DE LA EVALUACIÓN", datos_evaluacion)
    y -= 10
    
    # =========================================================
    # SECCIÓN 3: ANTECEDENTES (ANAMNESIS)
    # =========================================================
    if y < 180:
        c.showPage()
        y = height - 50
        dibujar_encabezado_pagina(c, height)
    
    # Limpiar descripciones de anamnesis
    items_anamnesis = []
    for h in anamnesis[:6]:
        desc = h['descripcion']
        # Limpiar texto: eliminar "Test:" o prefijos similares
        desc = desc.replace('Test:', '').replace('Anamnesis:', '').strip()
        if len(desc) > 80:
            desc = desc[:77] + "..."
        items_anamnesis.append(desc)
    
    y = dibujar_seccion_con_lista(c, y, "3. ANTECEDENTES CLÍNICOS (ANAMNESIS)", items_anamnesis)
    y -= 10
    
    # =========================================================
    # SECCIÓN 4: DIAGNÓSTICO CLÍNICO
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 50
        dibujar_encabezado_pagina(c, height)
    
    diagnostico = evaluacion.get('diagnostico_sistema', 'No disponible')
    y = dibujar_seccion_texto(c, y, "4. DIAGNÓSTICO CLÍNICO", diagnostico, color_fondo=(0.7, 0.2, 0.2), altura_extra=15)
    y -= 10
    
    # =========================================================
    # SECCIÓN 5: PRONÓSTICO
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 50
        dibujar_encabezado_pagina(c, height)
    
    pronostico = evaluacion.get('pronostico_sistema', 'No disponible')
    y = dibujar_seccion_texto(c, y, "5. PRONÓSTICO", pronostico, color_fondo=(0.2, 0.5, 0.2), altura_extra=15)
    y -= 10
    
    # =========================================================
    # SECCIÓN 6: PLAN DE INTERVENCIÓN
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 50
        dibujar_encabezado_pagina(c, height)
    
    ejercicios = evaluacion.get('sugerencia_ejercicios', 'No disponible')
    y = dibujar_seccion_texto(c, y, "6. PLAN DE INTERVENCIÓN", ejercicios, color_fondo=(0.2, 0.4, 0.6), altura_extra=15)
    y -= 15
    
    # =========================================================
    # SECCIÓN 7: TABLA DE RENDIMIENTO MFCC
    # =========================================================
    if y < 200:
        c.showPage()
        y = height - 70
        dibujar_encabezado_pagina(c, height)
    
    y = dibujar_tabla_mfcc_profesional(c, y, mfcc_scores)
    y -= 15
    
    # =========================================================
    # SECCIÓN 8: RECOMENDACIONES
    # =========================================================
    if y < 150:
        c.showPage()
        y = height - 50
        dibujar_encabezado_pagina(c, height)
    
    recomendaciones = [
        "Realizar los ejercicios recomendados en casa 3-4 veces por semana, en sesiones de 15-20 minutos.",
        "Mantener un ambiente tranquilo, sin televisión ni ruidos de fondo durante las prácticas.",
        "Reforzar positivamente cada logro del niño, por pequeño que sea.",
        "Consultar nuevamente si no se observan avances después de 8 semanas de práctica constante.",
        "Utilizar el chatbot 'AsistenteClínico' para resolver dudas sobre los ejercicios."
    ]
    
    y = dibujar_seccion_con_lista(c, y, "8. RECOMENDACIONES PARA EL TUTOR", recomendaciones, con_vistas=False)
    
    # =========================================================
    # PIE DE PÁGINA EN LA MISMA PÁGINA
    # =========================================================
    dibujar_pie_pagina_profesional(c, width, height, id_evaluacion, fecha_actual)
    
    c.save()
    return pdf_path


def dibujar_encabezado_pagina(c, height):
    """Dibuja el encabezado en páginas nuevas."""
    c.setFillColorRGB(0.0, 0.4, 0.6)
    c.rect(0, height-40, 612, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height-28, "SISTEMA EXPERTO DE FONOAUDIOLOGÍA CLÍNICA - BOLIVIA")
    c.setFont("Helvetica", 7)
    c.drawString(50, height-16, "Informe de Evaluación Fonoaudiológica")
    
    c.setStrokeColorRGB(0.0, 0.4, 0.6)
    c.setLineWidth(1.5)
    c.line(45, height-45, 567, height-45)


def dibujar_seccion_con_tabla(c, y, titulo, datos):
    """Dibuja una sección con tabla de 2 columnas con bordes."""
    # Fondo del título
    c.setFillColorRGB(0.2, 0.3, 0.5)
    c.rect(45, y-3, 520, 20, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y+2, titulo)
    y -= 18
    
    # Dibujar tabla
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 9)
    
    fila_y = y
    for i, (label, value) in enumerate(datos):
        if fila_y < 50:
            break
            
        # Borde de celda
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        c.rect(45, fila_y-12, 250, 14, fill=0)
        c.rect(295, fila_y-12, 270, 14, fill=0)
        
        # Contenido
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, fila_y-8, label)
        c.setFont("Helvetica", 9)
        valor_str = str(value)[:55] if len(str(value)) > 55 else str(value)
        c.drawString(300, fila_y-8, valor_str)
        
        fila_y -= 15
    
    return fila_y - 5


def dibujar_seccion_con_lista(c, y, titulo, items, con_vistas=True):
    """Dibuja una sección con lista de items."""
    # Fondo del título
    c.setFillColorRGB(0.2, 0.5, 0.3)
    c.rect(45, y-3, 520, 20, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y+2, titulo)
    y -= 18
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 9)
    
    for idx, item in enumerate(items, 1):
        if y < 50:
            break
        
        # Número o viñeta
        if con_vistas:
            c.setFillColorRGB(0.8, 0.9, 1)
            c.rect(48, y-2, 6, 6, fill=1)
            c.setFillColorRGB(0, 0, 0)
            prefijo = ""
        else:
            prefijo = f"{idx}. "
            c.setFillColorRGB(0, 0, 0)
        
        for line in formatear_texto_pdf(prefijo + item, 85):
            if y < 50:
                break
            if con_vistas:
                c.drawString(60, y-4, line)
            else:
                c.drawString(55, y-4, line)
            y -= 12
        y -= 3
    
    return y


def dibujar_seccion_texto(c, y, titulo, texto, color_fondo=None, altura_extra=0):
    """Dibuja una sección con texto formateado."""
    if color_fondo is None:
        color_fondo = (0.2, 0.3, 0.5)
    
    c.setFillColorRGB(*color_fondo)
    c.rect(45, y-3, 520, 20, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y+2, titulo)
    y -= 18
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 9)
    
    # Limpiar texto
    texto_limpio = texto.replace('**', '').replace('__', '')
    
    for line in formatear_texto_pdf(texto_limpio, 90):
        if y < 50:
            break
        c.drawString(55, y, line)
        y -= 12
    
    return y - altura_extra


def dibujar_tabla_mfcc_profesional(c, y, scores):
    """Dibuja tabla profesional de rendimiento MFCC con bordes."""
    # Título de la sección
    c.setFillColorRGB(0.3, 0.3, 0.5)
    c.rect(45, y-3, 520, 20, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y+2, "7. RENDIMIENTO POR FONEMA (Análisis Acústico MFCC)")
    y -= 20
    
    # Encabezados de tabla
    c.setFillColorRGB(0.2, 0.3, 0.5)
    c.rect(45, y-2, 520, 16, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y, "FONEMA")
    c.drawString(220, y, "PUNTAJE")
    c.drawString(320, y, "INTERPRETACIÓN CLÍNICA")
    c.drawString(490, y, "NIVEL")
    y -= 18
    
    # Filas de datos
    c.setFont("Helvetica", 9)
    fila_y = y
    row_count = 0
    
    # Si no hay scores, mostrar mensaje
    if not scores:
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(45, fila_y-2, 520, 20, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(55, fila_y, "No hay datos de evaluación MFCC disponibles")
        c.setFont("Helvetica", 9)
        return fila_y - 20
    
    for score in scores[:10]:
        valor = score['valor_obtenido'] if score['valor_obtenido'] is not None else 0
        # Limpiar nombre del fonema
        fonema = score['descripcion'] if score['descripcion'] else "Fonema"
        fonema = fonema.replace('Precisión en ', '').replace('/l/', 'L').replace('/r/', 'R').replace('/s/', 'S').strip()
        if len(fonema) > 22:
            fonema = fonema[:20] + "..."
        
        
        # Bordes de celda
       
        c.setLineWidth(0.3)
        c.rect(45, fila_y-2, 170, 14, fill=0)
        c.rect(215, fila_y-2, 100, 14, fill=0)
        c.rect(315, fila_y-2, 170, 14, fill=0)
        c.rect(485, fila_y-2, 80, 14, fill=0)
        
        # Contenido
        c.setFillColorRGB(0, 0, 0)
        c.drawString(55, fila_y-1, fonema)
        c.drawString(220, fila_y-1, f"{valor*100:.1f}%")
        
        # Interpretación con color
        if valor >= 0.7:
            interp = "Adecuado"
            nivel = "Alto"
            c.setFillColorRGB(0, 0.6, 0)
        elif valor >= 0.5:
            interp = "En proceso"
            nivel = "Medio"
            c.setFillColorRGB(0.8, 0.6, 0)
        elif valor >= 0.3:
            interp = "Requiere apoyo"
            nivel = "Bajo"
            c.setFillColorRGB(0.9, 0.5, 0)
        else:
            interp = "Déficit significativo"
            nivel = "Crítico"
            c.setFillColorRGB(0.8, 0.2, 0)
        
        c.drawString(330, fila_y-1, interp)
        c.drawString(500, fila_y-1, nivel)
        
        fila_y -= 15
        row_count += 1
        
        if fila_y < 60:
            fila_y -= 10
            c.setFont("Helvetica-Oblique", 7)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(55, fila_y, "Nota: Puntajes basados en análisis acústico MFCC. ≥70% = adecuado para edad")
            return fila_y - 15
    
    # Nota al pie
    if fila_y > 50:
        fila_y -= 8
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(55, fila_y, "Nota: Puntajes basados en análisis acústico MFCC. ≥70% = adecuado para edad")
    
    return fila_y - 15


def dibujar_pie_pagina_profesional(c, width, height, id_evaluacion, fecha_actual):
    """Dibuja el pie de página en la misma página."""
    # Línea separadora
    c.setStrokeColorRGB(0.0, 0.4, 0.6)
    c.setLineWidth(1)
    c.line(45, 55, width-45, 55)
    
    # Texto del pie
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(50, 42, "Documento generado por el Sistema Experto Fonoaudiológico - Centro de Fonoaudiología Bolivia")
    c.drawString(50, 32, "Este informe tiene carácter clínico y no sustituye la consulta presencial con un especialista.")
    
    # Código a la derecha
    codigo_texto = f"Código: INF-{id_evaluacion:04d} | Generado: {fecha_actual.strftime('%d/%m/%Y %H:%M')}"
    c.drawRightString(width-50, 42, codigo_texto)
    
    # Número de página
    c.drawRightString(width-50, 32, f"Página {c.getPageNumber()}")


def formatear_texto_pdf(texto: str, ancho_max: int = 90) -> list:
    """Formatea un texto para que quepa en el ancho especificado."""
    if not texto or texto == "No disponible":
        return ["No disponible"]
    
    # Limpiar caracteres especiales
    texto = texto.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    texto = texto.replace('**', '').replace('__', '').replace('✔', '')
    
    # Eliminar múltiples espacios
    import re
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    palabras = texto.split()
    lineas = []
    linea_actual = ""
    
    for palabra in palabras:
        linea_prueba = linea_actual + " " + palabra if linea_actual else palabra
        
        if len(linea_prueba) <= ancho_max:
            linea_actual = linea_prueba
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = palabra
    
    if linea_actual:
        lineas.append(linea_actual)
    
    return lineas if lineas else [texto[:ancho_max]]


def calcular_edad_exacta(fecha_nac: date) -> str:
    """Calcula edad exacta en años y meses."""
    hoy = datetime.now().date()
    años = hoy.year - fecha_nac.year
    meses = hoy.month - fecha_nac.month
    
    if meses < 0:
        años -= 1
        meses += 12
    
    if años > 0:
        return f"{años} año{'s' if años != 1 else ''} y {meses} mes{'es' if meses != 1 else ''}"
    else:
        return f"{meses} mes{'es' if meses != 1 else ''}"


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