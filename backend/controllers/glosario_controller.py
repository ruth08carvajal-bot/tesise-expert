from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from models.conexion_db import db_admin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/buscar")
async def buscar_en_glosario(
    q: Optional[str] = Query(None, description="Término a buscar"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    id_diag: Optional[int] = Query(None, description="Filtrar por diagnóstico asociado")
):
    """
    Busca términos en el glosario.
    - Si no hay query, devuelve todos los términos ordenados
    - Busca por coincidencia parcial en término técnico o amigable
    """
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    id_glosario,
                    termino_tecnico,
                    termino_amigable,
                    definicion_simple,
                    explicacion_detallada,
                    categoria,
                    id_diag,
                    palabra_clave,
                    imagen_url,
                    orden
                FROM glosario
                WHERE activo = 1
            """
            params = []
            
            if q:
                query += """ AND (
                    termino_tecnico LIKE %s 
                    OR termino_amigable LIKE %s 
                    OR palabra_clave LIKE %s
                )"""
                like = f"%{q}%"
                params.extend([like, like, like])
            
            if categoria:
                query += " AND categoria = %s"
                params.append(categoria)
            
            if id_diag:
                query += " AND id_diag = %s"
                params.append(id_diag)
            
            query += " ORDER BY orden ASC"
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            return {
                "status": "success",
                "total": len(resultados),
                "terminos": resultados
            }
            
    except Exception as e:
        logger.error(f"Error en glosario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/termino/{termino}")
async def obtener_termino(termino: str):
    """
    Obtiene un término específico del glosario por su nombre técnico
    """
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    id_glosario,
                    termino_tecnico,
                    termino_amigable,
                    definicion_simple,
                    explicacion_detallada,
                    categoria,
                    id_diag,
                    palabra_clave,
                    imagen_url
                FROM glosario
                WHERE termino_tecnico = %s AND activo = 1
            """, (termino,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                raise HTTPException(status_code=404, detail="Término no encontrado")
            
            return {
                "status": "success",
                "termino": resultado
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo término {termino}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categorias")
async def obtener_categorias():
    """
    Obtiene todas las categorías disponibles en el glosario
    """
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT DISTINCT categoria, COUNT(*) as cantidad
                FROM glosario
                WHERE activo = 1 AND categoria IS NOT NULL
                GROUP BY categoria
                ORDER BY categoria
            """)
            
            categorias = cursor.fetchall()
            
            return {
                "status": "success",
                "categorias": categorias
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/por-diagnostico/{id_diag}")
async def obtener_termino_por_diagnostico(id_diag: int):
    """
    Obtiene el término del glosario asociado a un diagnóstico específico
    """
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    g.termino_tecnico,
                    g.termino_amigable,
                    g.definicion_simple,
                    g.explicacion_detallada,
                    g.categoria,
                    d.nombre_diag as diagnostico_original
                FROM glosario g
                JOIN catalogo_diagnosticos d ON g.id_diag = d.id_diag
                WHERE g.id_diag = %s AND g.activo = 1
            """, (id_diag,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                return {
                    "status": "success",
                    "termino": None,
                    "mensaje": "No hay término en el glosario para este diagnóstico"
                }
            
            return {
                "status": "success",
                "termino": resultado
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo término para diagnóstico {id_diag}: {e}")
        raise HTTPException(status_code=500, detail=str(e))