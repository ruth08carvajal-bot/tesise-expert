from fastapi import APIRouter, HTTPException, Body
from models.conexion_db import db_admin
from schemas import NinoSchema, NinoUpdateSchema
from pydantic import BaseModel
from datetime import date, datetime
from utils.logger import get_logger
import traceback

logger = get_logger(__name__)

router = APIRouter()

# =========================================================
# FUNCIÓN CALCULAR EDAD
# =========================================================
def calcular_edad(fecha_nacimiento):
    if isinstance(fecha_nacimiento, str):
        fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))


def generar_usuario_unico(cursor, nombre_base: str) -> str:
    username = nombre_base.strip().lower().replace(' ', '.')
    contador = 1
    original_username = username
    while True:
        cursor.execute("SELECT id_user FROM usuario WHERE usr = %s", (username,))
        if not cursor.fetchone():
            return username
        username = f"{original_username}_{contador}"
        contador += 1


# =========================================================
# REGISTRAR NIÑO
# =========================================================
@router.post("/registrar-nino")
async def registrar_nino(nino: NinoSchema):
    try:
        logger.info("=" * 50)
        logger.info("DATOS RECIBIDOS EN EL BACKEND:")
        logger.info(f"nombre: {nino.nombre}")
        logger.info(f"id_tut: {nino.id_tut}")
        logger.info(f"f_nac: {nino.f_nac} (tipo: {type(nino.f_nac)})")
        logger.info(f"genero: {nino.genero}")
        logger.info(f"escolaridad: {nino.escolaridad}")
        logger.info(f"parentesco: {nino.parentesco}")
        logger.info("=" * 50)
        
        # Convertir fecha (porque en NinoSchema es string)
        fecha_nac = datetime.strptime(nino.f_nac, '%Y-%m-%d').date()
        logger.info(f"Fecha convertida: {fecha_nac}")
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # VALIDAR EDAD
            edad = calcular_edad(fecha_nac)
            logger.info(f"Edad calculada: {edad} años")
            
            if edad < 5:
                raise HTTPException(
                    status_code=400, 
                    detail=f"El niño debe tener al menos 5 años. Edad actual: {edad} años."
                )
            
            # Verificar si ya existe un niño con ese nombre para este tutor
            cursor.execute("SELECT id_nino FROM nino WHERE nombre = %s AND id_tut = %s", 
                          (nino.nombre, nino.id_tut))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un niño con el nombre '{nino.nombre}' para este tutor."
                )
            
            # Crear usuario para el niño con nombre de usuario único
            password = fecha_nac.strftime('%d/%m/%Y')
            usuario_unico = generar_usuario_unico(cursor, nino.nombre)
            logger.info(f"Usuario generado: {usuario_unico}")
            logger.info(f"Contraseña generada: {password}")
            
            cursor.execute(
                'INSERT INTO usuario (usr, psw, id_rol, estado) VALUES (%s, %s, 3, "activo")', 
                (usuario_unico, password)
            )
            id_user = cursor.lastrowid
            logger.info(f"Usuario creado con ID: {id_user}")
            
            # Guardar el niño
            query = """
                INSERT INTO nino (id_user, id_tut, nombre, f_nac, genero, escolaridad, parentesco) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_user, nino.id_tut, nino.nombre, fecha_nac, 
                nino.genero, nino.escolaridad, nino.parentesco
            ))
            conn.commit()
            
            id_nino_creado = cursor.lastrowid
            logger.info(f"Niño creado con ID: {id_nino_creado}")
            
            return {
                "status": "success",
                "id_nino": id_nino_creado,
                "username": usuario_unico,
                "password": password
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando niño: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


class SimpleTestSchema(BaseModel):
    test: str

class NinoUpdateSchemaInline(BaseModel):
    nombre: str
    f_nac: str
    genero: str
    escolaridad: str
    parentesco: str

class NinoUpdateSchemaInline(BaseModel):
    nombre: str
    f_nac: str
    genero: str
    escolaridad: str
    parentesco: str

class TwoFieldSchema(BaseModel):
    nombre: str
    f_nac: str

class ThreeFieldSchema(BaseModel):
    nombre: str
    f_nac: str
    genero: str

class FourFieldSchema(BaseModel):
    nombre: str
    f_nac: str
    genero: str
    escolaridad: str

class FiveFieldSchema(BaseModel):
    nombre: str
    f_nac: str
    genero: str
    escolaridad: str
    parentesco: str


# =========================================================
# LISTAR NIÑOS DE UN TUTOR
# =========================================================
@router.get("/mis-ninos/{id_tut}")
async def listar_ninos(id_tut: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT n.id_nino, n.nombre, n.f_nac, n.genero, n.escolaridad, n.parentesco,
                   COALESCE((SELECT COUNT(*) FROM anamnesis_hechos a WHERE a.id_nino = n.id_nino), 0) as anamnesis_completa,
                   COALESCE((SELECT COUNT(*) FROM evaluacion_sesion e WHERE e.id_nino = n.id_nino), 0) as tiene_evaluaciones,
                   COALESCE((SELECT MAX(id_ev) FROM evaluacion_sesion e WHERE e.id_nino = n.id_nino), 0) as ultima_eval_id,
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
            FROM nino n 
            WHERE n.id_tut = %s
        """
        cursor.execute(query, (id_tut,))
        ninos = cursor.fetchall()
        
        # Procesar cada niño para calcular si puede ser reevaluado
        for nino in ninos:
            if nino.get('ultima_eval_id') and nino['ultima_eval_id'] > 0:
                cursor.execute("""
                    SELECT fecha_eval FROM evaluacion_sesion 
                    WHERE id_ev = %s
                """, (nino['ultima_eval_id'],))
                ultima = cursor.fetchone()
                if ultima and ultima['fecha_eval']:
                    fecha_ultima = ultima['fecha_eval']
                    hoy = date.today()
                    if isinstance(fecha_ultima, datetime):
                        fecha_ultima = fecha_ultima.date()
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


# =========================================================
# OBTENER UN NIÑO POR ID
# =========================================================
@router.get("/nino/{id_nino}")
async def obtener_nino(id_nino: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT n.id_nino, n.nombre, n.f_nac, n.genero, n.escolaridad, n.parentesco, u.usr AS username, u.psw AS password "
            "FROM nino n JOIN usuario u ON n.id_user = u.id_user WHERE n.id_nino = %s",
            (id_nino,)
        )
        nino = cursor.fetchone()
        if not nino:
            raise HTTPException(status_code=404, detail="Niño no encontrado")
        nino['edad'] = calcular_edad(nino['f_nac'])
        return nino


# =========================================================
@router.put("/actualizar-nino/{id_nino}")
async def actualizar_nino(id_nino: int, datos: NinoUpdateSchema):
    try:
        logger.info(f"Actualizando niño {id_nino} con datos: {datos}")
        fecha_nac = datetime.strptime(datos.f_nac, '%Y-%m-%d').date()
        edad = calcular_edad(fecha_nac)
        logger.info(f"Edad calculada al actualizar: {edad} años")
        if edad < 5 or edad > 10:
            raise HTTPException(
                status_code=400,
                detail=f"El niño debe tener entre 5 y 10 años. Edad actual: {edad} años."
            )

        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_tut FROM nino WHERE id_nino = %s", (id_nino,))
            nino_existente = cursor.fetchone()
            if not nino_existente:
                raise HTTPException(status_code=404, detail="Niño no encontrado")

            id_tut = nino_existente['id_tut']
            cursor.execute(
                "SELECT id_nino FROM nino WHERE nombre = %s AND id_tut = %s AND id_nino != %s",
                (datos.nombre, id_tut, id_nino)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Ya existe otro niño con el nombre '{datos.nombre}' para este tutor.")

            cursor.execute(
                "UPDATE nino SET nombre=%s, f_nac=%s, genero=%s, escolaridad=%s, parentesco=%s WHERE id_nino=%s",
                (datos.nombre, fecha_nac, datos.genero, datos.escolaridad, datos.parentesco, id_nino)
            )
            conn.commit()
            logger.info(f"Niño {id_nino} actualizado en la BD exitosamente")

            cursor.execute(
                "SELECT u.usr as username, u.psw as password FROM nino n JOIN usuario u ON n.id_user = u.id_user WHERE n.id_nino = %s",
                (id_nino,)
            )
            credenciales = cursor.fetchone()
            return {
                "status": "success",
                "id_nino": id_nino,
                "username": credenciales['username'],
                "password": credenciales['password']
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando niño: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
