from fastapi import APIRouter, HTTPException
from models.conexion_db import db_admin
from pydantic import BaseModel
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class LoginSchema(BaseModel):
    username: str
    password: str

class RegisterSchema(BaseModel):
    nombre_completo: str
    username: str
    password: str
    email: str
    celular: str
    ocupacion: str
    zona: str

#@router.post("/login")
#async def login(datos: LoginSchema):
#    with db_admin.obtener_conexion() as conn:
#        cursor = conn.cursor(dictionary=True)
#        # Ajustado a tus columnas: id_user, usr, psw
#        query = """
#            SELECT u.id_user, u.usr, u.id_rol, t.nombre, t.id_tut 
#            FROM usuario u
#            LEFT JOIN tutor t ON u.id_user = t.id_user
#            WHERE u.usr = %s AND u.psw = %s
#        """
#        cursor.execute(query, (datos.username, datos.password))
#        usuario = cursor.fetchone()
#        
#        if not usuario:
#            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
#        
#        return {"status": "success", "usuario": usuario}
# inicio nuevo login con roles y datos completos
@router.post("/login")
async def login(datos: LoginSchema):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Buscar usuario por username y password
        query = """
            SELECT u.id_user, u.usr, u.id_rol, u.estado
            FROM usuario u
            WHERE u.usr = %s AND u.psw = %s
        """
        cursor.execute(query, (datos.username, datos.password))
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        if usuario['estado'] != 'activo':
            raise HTTPException(status_code=401, detail="Usuario inactivo")
        
        # =========================================================
        # Si es TUTOR (rol=2) - Obtener datos del tutor
        # =========================================================
        if usuario['id_rol'] == 2:
            cursor.execute("""
                SELECT id_tut, nombre, email, celular, ocupacion, zona
                FROM tutor
                WHERE id_user = %s
            """, (usuario['id_user'],))
            tutor = cursor.fetchone()
            
            if not tutor:
                raise HTTPException(status_code=404, detail="Datos de tutor no encontrados")
            
            return {
                "status": "success",
                "usuario": {
                    "id_user": usuario['id_user'],
                    "username": usuario['usr'],
                    "id_rol": 2,
                    "rol": "tutor",
                    "id_tut": tutor['id_tut'],
                    "nombre": tutor['nombre'],
                    "email": tutor['email'],
                    "celular": tutor['celular'],
                    "ocupacion": tutor['ocupacion'],
                    "zona": tutor['zona']
                }
            }
        
        # =========================================================
        # Si es NIÑO (rol=3) - Obtener datos del niño
        # =========================================================
        elif usuario['id_rol'] == 3:
            cursor.execute("""
                SELECT n.id_nino, n.nombre, n.f_nac, n.genero, n.escolaridad,
                       t.id_tut, t.nombre as tutor_nombre
                FROM nino n
                JOIN tutor t ON n.id_tut = t.id_tut
                WHERE n.id_user = %s
            """, (usuario['id_user'],))
            nino = cursor.fetchone()
            
            if not nino:
                raise HTTPException(status_code=404, detail="Datos del niño no encontrados")
            
            return {
                "status": "success",
                "usuario": {
                    "id_user": usuario['id_user'],
                    "username": usuario['usr'],
                    "id_rol": 3,
                    "rol": "nino",
                    "id_nino": nino['id_nino'],
                    "nombre": nino['nombre'],
                    "f_nac": nino['f_nac'].strftime('%Y-%m-%d'),
                    "genero": nino['genero'],
                    "escolaridad": nino['escolaridad'],
                    "tutor_id": nino['id_tut'],
                    "tutor_nombre": nino['tutor_nombre']
                }
            }
        
        # =========================================================
        # Si es ADMIN (rol=1) - Por implementar
        # =========================================================
        else:
            return {
                "status": "success",
                "usuario": {
                    "id_user": usuario['id_user'],
                    "username": usuario['usr'],
                    "id_rol": 1,
                    "rol": "admin"
                }
            }
# fin nuevo login con roles y datos completos 26/04/2026
@router.post("/register")
async def register(datos: RegisterSchema):
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # 1. Insertar en tabla 'usuario'
            query_user = "INSERT INTO usuario (usr, psw, id_rol) VALUES (%s, %s, 2)"
            cursor.execute(query_user, (datos.username, datos.password))
            id_nuevo_usuario = cursor.lastrowid

            # 2. Insertar en tabla 'tutor' con todos los datos de la ficha
            query_tutor = """
                INSERT INTO tutor (id_user, nombre, email, celular, ocupacion, zona) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_tutor, (
                id_nuevo_usuario, 
                datos.nombre_completo, 
                datos.email, 
                datos.celular, 
                datos.ocupacion, 
                datos.zona
            ))
            
            conn.commit()
            return {"status": "success", "username_generado": datos.username}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")