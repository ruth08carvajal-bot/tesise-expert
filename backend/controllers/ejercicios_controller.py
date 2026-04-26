from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.conexion_db import db_admin
from controllers.ninos_controller import calcular_edad
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class GuardarProgresoSchema(BaseModel):
    id_nino: int
    id_ejercicio: int
    puntaje_obtenido: float
    tiempo_empleado: int  # en segundos


@router.get("/mis-ejercicios/{id_nino}")
async def obtener_ejercicios_nino(id_nino: int):
    """
    Obtiene los ejercicios recomendados para un niño específico.
    Similar al plan-evaluacion pero adaptado para el niño.
    """
    try:
        from controllers.evaluacion_controller import construir_plan_personalizado
        
        plan = construir_plan_personalizado(id_nino)
        
        # Formatear para el niño
        ejercicios = []
        for ej in plan.get('plan_adaptativo', []):
            ejercicios.append({
                "id_ejercicio": ej.get('id_ejercicio'),
                "nombre": ej.get('nombre_ejercicio'),
                "descripcion": ej.get('descripcion_instrucciones'),
                "nivel": ej.get('nivel_dificultad'),
                "tipo_apoyo": ej.get('tipo_apoyo'),
                "id_hecho_objetivo": ej.get('id_hecho_objetivo'),
                "rendimiento_previo": ej.get('rendimiento', 0)
            })
        
        # Obtener edad del niño
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT f_nac, nombre FROM nino WHERE id_nino = %s", (id_nino,))
            nino = cursor.fetchone()
            edad = calcular_edad(nino['f_nac']) if nino else 0
        
        return {
            "status": "success",
            "id_nino": id_nino,
            "nombre_nino": nino['nombre'] if nino else "",
            "edad_nino": edad,
            "ejercicios": ejercicios
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo ejercicios para niño {id_nino}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guardar-progreso")
async def guardar_progreso(datos: GuardarProgresoSchema):
    """
    Guarda el progreso de un niño en un ejercicio.
    Actualiza rendimiento_hecho y progreso_nino.
    """
    try:
        # Validar puntaje
        if not 0 <= datos.puntaje_obtenido <= 1:
            raise HTTPException(status_code=400, detail="Puntaje debe estar entre 0 y 1")
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # 1. Guardar en progreso_nino (historial de intentos)
            query_progreso = """
                INSERT INTO progreso_nino 
                (id_nino, id_ejercicio, puntaje_obtenido, tiempo_empleado, intento_numero, estado_actual)
                VALUES (%s, %s, %s, %s, 
                    (SELECT COALESCE(MAX(intento_numero), 0) + 1 FROM progreso_nino WHERE id_nino = %s AND id_ejercicio = %s),
                    'completado'
                )
            """
            cursor.execute(query_progreso, (
                datos.id_nino, datos.id_ejercicio, datos.puntaje_obtenido, 
                datos.tiempo_empleado, datos.id_nino, datos.id_ejercicio
            ))
            
            # 2. Obtener el id_hecho asociado a este ejercicio
            cursor.execute("""
                SELECT id_hecho_objetivo FROM catalogo_ejercicios WHERE id_ejercicio = %s
            """, (datos.id_ejercicio,))
            resultado = cursor.fetchone()
            
            if resultado and resultado[0]:
                id_hecho = resultado[0]
                
                # 3. Actualizar rendimiento_hecho (promedio histórico)
                from controllers.evaluacion_controller import actualizar_rendimiento
                actualizar_rendimiento(datos.id_nino, id_hecho, datos.puntaje_obtenido)
            
            conn.commit()
            
            # 4. Calcular nuevo nivel basado en rendimiento (ZPD)
            nuevo_nivel = _calcular_nivel_adaptativo(datos.id_nino, datos.id_ejercicio)
            
            return {
                "status": "success",
                "mensaje": "Progreso guardado correctamente",
                "puntaje": datos.puntaje_obtenido,
                "nivel_sugerido": nuevo_nivel
            }
            
    except Exception as e:
        logger.error(f"Error guardando progreso: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sesion-practica/{id_nino}")
async def obtener_sesion_practica(id_nino: int):
    """Obtiene o crea una sesión de práctica (no reevaluación)"""
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Buscar sesión de práctica existente (tipo 'Practica')
            cursor.execute("""
                SELECT id_ev FROM evaluacion_sesion 
                WHERE id_nino = %s AND tipo_evaluacion = 'Practica'
                LIMIT 1
            """, (id_nino,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                id_evaluacion = resultado[0]
            else:
                # Crear nueva sesión de práctica
                cursor.execute("""
                    INSERT INTO evaluacion_sesion (id_nino, tipo_evaluacion, notas_tutor)
                    VALUES (%s, 'Practica', 'Sesión de práctica libre del niño')
                """, (id_nino,))
                id_evaluacion = cursor.lastrowid
                conn.commit()
            
            return {
                "status": "success",
                "id_evaluacion": id_evaluacion
            }
            
    except Exception as e:
        logger.error(f"Error creando sesión de práctica: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
def _calcular_nivel_adaptativo(id_nino: int, id_ejercicio: int) -> str:
    """Calcula el nivel recomendado basado en los últimos 5 intentos."""
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener últimos 5 puntajes
            cursor.execute("""
                SELECT puntaje_obtenido
                FROM progreso_nino
                WHERE id_nino = %s AND id_ejercicio = %s
                ORDER BY fecha_realizacion DESC
                LIMIT 5
            """, (id_nino, id_ejercicio))
            
            puntajes = [p['puntaje_obtenido'] for p in cursor.fetchall()]
            
            if not puntajes:
                return "Bajo"
            
            promedio = sum(puntajes) / len(puntajes)
            
            if promedio >= 0.7:
                return "Alto"
            elif promedio >= 0.4:
                return "Medio"
            else:
                return "Bajo"
                
    except Exception as e:
        logger.error(f"Error calculando nivel adaptativo: {e}")
        return "Medio"