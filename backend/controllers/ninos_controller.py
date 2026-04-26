from fastapi import APIRouter, HTTPException
from models.conexion_db import db_admin
from pydantic import BaseModel
from datetime import date, datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def calcular_edad(fecha_nacimiento):
    if isinstance(fecha_nacimiento, str):
        fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

class NinoSchema(BaseModel):
    id_tut: int
    nombre: str
    f_nac: date
    genero: str
    escolaridad: str
    parentesco: str

@router.post("/registrar-nino")
async def registrar_nino(nino: NinoSchema):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            # Crear usuario para el niño
            password = nino.f_nac.strftime('%d/%m/%Y')
            cursor.execute('INSERT INTO usuario (usr, psw, id_rol) VALUES (%s, %s, 3)', (nino.nombre, password))
            id_user = cursor.lastrowid
            # Guardar el niño
            query = """
                INSERT INTO nino (id_user, id_tut, nombre, f_nac, genero, escolaridad, parentesco) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_user, nino.id_tut, nino.nombre, nino.f_nac, 
                nino.genero, nino.escolaridad, nino.parentesco
            ))
            conn.commit()
            return {"status": "success", "id_nino": cursor.lastrowid}
    except Exception as e:
        logger.error(f"Error registrando niño: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/mis-ninos/{id_tut}")
async def listar_ninos(id_tut: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        # Query con subqueries para anamnesis y evaluaciones
        query = """
            SELECT n.id_nino, n.nombre, n.f_nac, n.genero, n.escolaridad, n.parentesco,
                   COALESCE((SELECT COUNT(*) FROM anamnesis_hechos a WHERE a.id_nino = n.id_nino), 0) as anamnesis_completa,
                   COALESCE((SELECT COUNT(*) FROM evaluacion_sesion e WHERE e.id_nino = n.id_nino), 0) as tiene_evaluaciones,
                   COALESCE((SELECT MAX(id_ev) FROM evaluacion_sesion e WHERE e.id_nino = n.id_nino), 0) as ultima_eval_id,
                   # inicio subquery evaluaciones 26-06-2024
                   (
                        SELECT JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'id_ev', e.id_ev, 
                                'fecha', e.fecha_eval, 
                                'tipo', e.tipo_evaluacion,
                                'fecha_formateada', DATE_FORMAT(e.fecha_eval, '%d/%m/%Y')
                            )
                        ) 
                        FROM evaluacion_sesion e 
                        WHERE e.id_nino = n.id_nino
                        ORDER BY e.fecha_eval DESC
                    ) as evaluaciones
                    # fin subquery evaluaciones 26-06-2024
            FROM nino n 
            WHERE n.id_tut = %s
        """
        cursor.execute(query, (id_tut,))
        return cursor.fetchall()
        # inicio Procesar cada niño para calcular si puede ser reevaluado 26-06-2024
        from datetime import date
        from controllers.ninos_controller import calcular_edad
        
        for nino in ninos:
            # Calcular meses desde última evaluación
            if nino.get('ultima_eval_id') and nino['ultima_eval_id'] > 0:
                cursor.execute("""
                    SELECT fecha_eval FROM evaluacion_sesion 
                    WHERE id_ev = %s
                """, (nino['ultima_eval_id'],))
                ultima = cursor.fetchone()
                if ultima and ultima['fecha_eval']:
                    fecha_ultima = ultima['fecha_eval']
                    hoy = date.today()
                    meses_diferencia = (hoy.year - fecha_ultima.year) * 12 + (hoy.month - fecha_ultima.month)
                    nino['meses_desde_ultima_eval'] = meses_diferencia
                    nino['puede_reevaluar'] = meses_diferencia >= 3
                    nino['meses_restantes'] = max(0, 3 - meses_diferencia)
                else:
                    nino['puede_reevaluar'] = True
                    nino['meses_desde_ultima_eval'] = 0
                    nino['meses_restantes'] = 0
            else:
                nino['puede_reevaluar'] = True
                nino['meses_desde_ultima_eval'] = 0
                nino['meses_restantes'] = 0
        
        return ninos
    # fin Procesar cada niño para calcular si puede ser reevaluado 26-06-2024
