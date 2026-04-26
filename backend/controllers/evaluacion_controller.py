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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
mfcc_service = MFCCService()
motor = MotorInferencia()
explicacion_service = ExplicacionService()

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


def niveles_permitidos_por_edad(edad: int):
    if edad < 5:
        return ['Bajo']
    if edad < 7:
        return ['Bajo', 'Medio']
    return ['Bajo', 'Medio', 'Alto']


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
        return {"status": "success", **informe}
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


def generar_pdf_clinico(id_nino: int, id_evaluacion: int) -> str:
    informe = obtener_informe_clinico(id_nino, id_evaluacion)
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, f"reporte_clinico_{id_nino}_{id_evaluacion}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Informe Clínico - Niño {id_nino}")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Evaluación: {id_evaluacion}    Edad: {obtener_edad_nino(id_nino)} años")
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resumen clínico:")
    y -= 20
    text = c.beginText(50, y)
    text.setFont("Helvetica", 10)
    for line in explicacion_service.formatear_parrafo(informe['explicacion_general']).split("\n"):
        text.textLine(line)
        y -= 14
        if y < 80:
            c.drawText(text)
            c.showPage()
            y = height - 60
            text = c.beginText(50, y)
            text.setFont("Helvetica", 10)
    c.drawText(text)
    y = text.getY() - 20

    c.setFont("Helvetica-Bold", 12)
    if y < 150:
        c.showPage()
        y = height - 60
    c.drawString(50, y, "Anamnesis relevante:")
    y -= 20
    c.setFont("Helvetica", 10)
    for item in informe['anamnesis']:
        c.drawString(60, y, f"- {item.get('descripcion', '')}")
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 60
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Diagnósticos detectados:")
    y -= 20
    c.setFont("Helvetica", 10)
    for diag in informe['diagnosticos']:
        c.drawString(60, y, f"- {diag.get('nombre', 'Diagnóstico')} ({round(diag.get('certeza', 0)*100, 1)}%)")
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 60
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Plan de intervención:")
    y -= 20
    c.setFont("Helvetica", 10)
    for exercise in informe['plan'][:15]:
        c.drawString(60, y, f"- {exercise.get('nombre', 'Ejercicio')} (Nivel: {exercise.get('nivel_dificultad', '')})")
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 60
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Puntajes MFCC clave:")
    y -= 20
    c.setFont("Helvetica", 10)
    for score in informe['mfcc_scores'][:10]:
        c.drawString(60, y, f"- {score.get('descripcion', '')}: {round(score.get('score', 0), 3)}")
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 60

    c.showPage()
    c.save()
    return pdf_path


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