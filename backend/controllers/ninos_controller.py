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
                   COALESCE((SELECT MAX(id_ev) FROM evaluacion_sesion e WHERE e.id_nino = n.id_nino), 0) as ultima_eval_id
            FROM nino n 
            WHERE n.id_tut = %s
        """
        cursor.execute(query, (id_tut,))
        return cursor.fetchall()