from fastapi import APIRouter, HTTPException
from models.conexion_db import db_admin
from datetime import date, datetime
import logging
# Importamos la función desde tu controlador de niños
from controllers.ninos_controller import calcular_edad

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/preguntas-anamnesis/{id_nino}")
async def obtener_preguntas_dinamicas(id_nino: int):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Obtener datos del niño para calcular la edad
            cursor.execute("SELECT f_nac, nombre FROM nino WHERE id_nino = %s", (id_nino,))
            nino = cursor.fetchone()
            
            if not nino:
                raise HTTPException(status_code=404, detail="Niño no encontrado")
            
            edad = calcular_edad(nino['f_nac'])
            nombre_nino = nino['nombre']
            
            # 2. Traer preguntas usando ALIAS (AS) para que coincida con tu Frontend
            # Tu React busca "p.descripcion_hecho", por eso usamos "descripcion AS descripcion_hecho"
            query = """
                SELECT 
                    id_hecho, 
                    cod_h, 
                    descripcion AS descripcion_hecho, 
                    categoria_clinica AS categoria 
                FROM base_hechos 
                WHERE instrumento_origen IN ('Tutor', 'Social')
            """
            cursor.execute(query)
            preguntas = cursor.fetchall()
            
            preguntas_filtradas = []
            
            # 3. Filtrado lógico basado en los IDs de tu base de datos
            for p in preguntas:
                id_h = p['id_hecho']
                
                # H123: Muda de dientes incisivos (Solo niños >= 6 años)
                if id_h == 123 and edad < 6: continue
                
                # H115: Errores lectura / H125: Errores escritura (Solo >= 7 años)
                if id_h in [115, 125] and edad < 7: continue
                
                # H135: Interpretación literal/bromas (Solo >= 7 años)
                if id_h == 135 and edad < 7: continue

                # H113: Ausencia vibración lingual (Solo >= 5 años)
                if id_h == 113 and edad < 5: continue

                preguntas_filtradas.append(p)
                
            return {
                "id_nino": id_nino,
                "nombre_nino": nombre_nino,
                "edad_nino": edad, 
                "preguntas": preguntas_filtradas
            }

    except Exception as e:
        logger.error(f"Error obteniendo preguntas dinámicas para id_nino={id_nino}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")

@router.post("/guardar-anamnesis")
async def guardar_anamnesis(data: dict):
    id_nino = data.get("id_nino")
    hechos_presentes = data.get("hechos_presentes", []) # Lista de IDs enviados desde React
    
    if not id_nino:
        raise HTTPException(status_code=400, detail="id_nino es requerido")
    
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Limpiar respuestas previas para evitar duplicados
            cursor.execute("DELETE FROM anamnesis_hechos WHERE id_nino = %s", (id_nino,))
            
            # Insertar los hechos marcados como "Presente"
            query_insert = "INSERT INTO anamnesis_hechos (id_nino, id_hecho, valor_presencia) VALUES (%s, %s, 1)"
            
            for id_hecho in hechos_presentes:
                cursor.execute(query_insert, (id_nino, id_hecho))
            
            conn.commit()
            return {"status": "success", "message": "Resultados guardados correctamente"}
            
    except Exception as e:
        logger.error(f"Error guardando anamnesis para id_nino={id_nino}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al guardar en la base de datos")