from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from services.mfcc_service import MFCCService
from services.motor_inferencia import MotorInferencia
from models.conexion_db import db_admin
import shutil
import os
import subprocess

router = APIRouter()
mfcc_service = MFCCService()
motor = MotorInferencia()

class EvaluacionManual(BaseModel):
    id_nino: int
    id_evaluacion: int
    id_hecho: int
    valor: float
    #id_tipo_evidencia: Optional[int] = None nuevo 23/04/26, lo dejamos fijo en el endpoint para no complicar el front con esta lógica
def obtener_id_tipo_evidencia(nombre_tipo: str):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_tipo FROM tipo_evidencia WHERE nombre = %s",
            (nombre_tipo,)
        )
        result = cursor.fetchone()
        if not result:
            raise Exception(f"Tipo de evidencia '{nombre_tipo}' no existe")
        return result[0]
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluar-fonema")
async def evaluar_fonema(
    id_nino: int = Form(...),
    id_evaluacion: int = Form(...),
    fonema_objetivo: str = Form(...), # Este es el id_hecho que viene del front
    audio: UploadFile = File(...)
):
    try:
        # 1. Mapeo y procesamiento de audio
        nombre_fonema = mapear_id_a_nombre(fonema_objetivo)
        os.makedirs("data/temp_audios", exist_ok=True)
        
        # Guardamos con la extensión que venga (.webm o .ogg habitualmente)
        ext = audio.filename.split('.')[-1]
        audio_path = f"data/temp_audios/{id_nino}_{nombre_fonema}.{ext}"
        
        await audio.seek(0)
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Convertir a WAV si es necesario
        if ext.lower() in ['webm', 'ogg', 'mp3']:
            wav_path = audio_path.replace(f'.{ext}', '.wav')
            try:
                ffmpeg_path = r"C:\Program Files\GNU Octave\Octave-8.3.0\mingw64\bin\ffmpeg.exe"
                #ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
                # AÑADIMOS '-y' al inicio de la lista de argumentos
                subprocess.run([ffmpeg_path, '-y','-i', audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path], check=True)
                audio_path = wav_path
                os.remove(audio_path.replace('.wav', f'.{ext}'))  # Eliminar el original
            except subprocess.CalledProcessError as e:
                print(f"Error convirtiendo audio: {e}")
                raise HTTPException(status_code=500, detail="Error procesando el audio")
        # 2. Obtener resultado del MFCC
        porcentaje_similitud = mfcc_service.procesar_evaluacion(
            audio_nino_path=audio_path, 
            fonema=nombre_fonema, 
            id_ev=id_evaluacion
        )
        # nuevo: actualizar rendimiento histórico
        actualizar_rendimiento(id_nino, int(fonema_objetivo), porcentaje_similitud)
        # 3. ¡NUEVO!: PERSISTENCIA EN MEMORIA DE TRABAJO
                # CORRECCIÓN: ahora obtenemos id_tipo_evidencia dinámicamente para no hardcodear el '4' y que sea más flexible a cambios futuros 23/04/26
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()

            id_tipo = obtener_id_tipo_evidencia("MFCC")

            query_memoria = """
                INSERT INTO memoria_trabajo 
                (id_ev, id_hecho, valor_obtenido, id_tipo_evidencia, confiabilidad, fuente) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE valor_obtenido = %s
            """

            cursor.execute(query_memoria, (
                id_evaluacion,
                fonema_objetivo,
                porcentaje_similitud,
                id_tipo,
                0.9,            # confiabilidad MFCC
                "MFCC",
                porcentaje_similitud
            ))

            conn.commit() # fin de la corrección para obtener id_tipo_evidencia dinámicamente

        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {
            "status": "success",
            "similitud_detectada": round(porcentaje_similitud, 4),
            "id_hecho": fonema_objetivo,
            "fonema_evaluado": nombre_fonema
        }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# CORRECCIÓN: ahora el endpoint de evaluación manual también actualiza el rendimiento histórico y obtiene id_tipo_evidencia dinámicamente para mantener consistencia con el endpoint de evaluación automática 23/04/26
@router.post("/evaluar-manual")
async def evaluar_manual(datos: EvaluacionManual):
    try:
        actualizar_rendimiento(datos.id_nino, datos.id_hecho, datos.valor)

        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()

            # Puedes decidir si esto es FUZZY o OTRO
            # Aquí lo pongo como OTRO (evaluación directa)
            id_tipo = obtener_id_tipo_evidencia("OTRO")

            query = """
                INSERT INTO memoria_trabajo 
                (id_ev, id_hecho, valor_obtenido, id_tipo_evidencia, confiabilidad, fuente) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE valor_obtenido = %s
            """

            cursor.execute(query, (
                datos.id_evaluacion,
                datos.id_hecho,
                datos.valor,
                id_tipo,
                1.0,            # máxima confiabilidad
                "MANUAL",
                datos.valor
            ))

            conn.commit()

        return {"status": "success", "similitud_detectada": datos.valor}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
        
def mapear_id_a_nombre(entrada):
    mapeo_inv = {'1': 'r', '2': 'ere', '3': 's', '4': 'l', '5': 'c', '6': 't', '7': 'd', '8': 'p', '9': 'b', '10': 'g', '14': 'f', '16': 'ch'}
    return mapeo_inv.get(str(entrada), entrada)
# controllers/evaluacion_controller.py

# controllers/evaluacion_controller.py

@router.get("/ejecutar-diagnostico/{id_nino}/{id_evaluacion}")
async def ejecutar_diagnostico(id_nino: int, id_evaluacion: int):
    try:
        # Usamos el método de tu Motor de Inferencia
        resultados = motor.ejecutar_diagnostico_completo(id_nino, id_evaluacion)
        return {"status": "success", "diagnosticos": resultados}
    except Exception as e:
        print(f"Error en motor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# nueva función para actualizar rendimiento después de cada evaluación
def actualizar_rendimiento(id_nino, id_hecho, nuevo_valor):
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

            #tendencia = "Sube" if nuevo_valor > promedio_actual else "Baja"
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