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
    fonema_objetivo: str = Form(...),
    audio: UploadFile = File(...)
):
    try:
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
                # AÑADIMOS '-y' al inicio de la lista de argumentos
                subprocess.run([ffmpeg_path, '-y','-i', audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path], check=True)
                audio_path = wav_path
                os.remove(audio_path.replace('.wav', f'.{ext}'))  # Eliminar el original
            except subprocess.CalledProcessError as e:
                print(f"Error convirtiendo audio: {e}")
                raise HTTPException(status_code=500, detail="Error procesando el audio")

        porcentaje_similitud = mfcc_service.procesar_evaluacion(
            audio_nino_path=audio_path, 
            fonema=nombre_fonema, 
            id_ev=id_evaluacion
        )

        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {
            "status": "success",
            "similitud_detectada": round(porcentaje_similitud, 4),
            "fonema_evaluado": nombre_fonema
        }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluar-manual")
async def evaluar_manual(datos: EvaluacionManual):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO memoria_trabajo (id_ev, id_hecho, valor_obtenido) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE valor_obtenido = %s
            """
            cursor.execute(query, (datos.id_evaluacion, datos.id_hecho, datos.valor, datos.valor))
            conn.commit()
        return {"status": "success", "similitud_detectada": datos.valor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan-evaluacion/{id_nino}")
async def obtener_plan_personalizado(id_nino: int):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            query_ana = "SELECT id_hecho FROM anamnesis_hechos WHERE id_nino = %s"
            cursor.execute(query_ana, (id_nino,))
            hechos_padre = [row['id_hecho'] for row in cursor.fetchall()]

            if hechos_padre:
                format_strings = ','.join(['%s'] * len(hechos_padre))
                query_plan = f"""
                    SELECT DISTINCT e.* FROM catalogo_ejercicios e
                    LEFT JOIN base_reglas r ON e.id_ejercicio = r.id_ejercicio_sugerido
                    WHERE r.id_hecho IN ({format_strings})
                    OR e.nivel_dificultad = 'Bajo'
                """
                cursor.execute(query_plan, tuple(hechos_padre))
            else:
                cursor.execute("SELECT * FROM catalogo_ejercicios WHERE nivel_dificultad = 'Bajo'")
            
            ejercicios = cursor.fetchall()
            return {"id_nino": id_nino, "plan_evaluacion": ejercicios}
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