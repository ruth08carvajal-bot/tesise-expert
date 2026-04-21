from fastapi import APIRouter, HTTPException
from models.conexion_db import db_admin
from pydantic import BaseModel

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

@router.post("/login")
async def login(datos: LoginSchema):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        # Ajustado a tus columnas: id_user, usr, psw
        query = """
            SELECT u.id_user, u.usr, u.id_rol, t.nombre, t.id_tut 
            FROM usuario u
            LEFT JOIN tutor t ON u.id_user = t.id_user
            WHERE u.usr = %s AND u.psw = %s
        """
        cursor.execute(query, (datos.username, datos.password))
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        return {"status": "success", "usuario": usuario}

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
        raise HTTPException(status_code=500, detail=str(e))