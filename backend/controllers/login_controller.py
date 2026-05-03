from fastapi import APIRouter, HTTPException
from models.conexion_db import db_admin
from schemas import LoginSchema
from utils.logger import get_logger
import traceback

logger = get_logger(__name__)

router = APIRouter()

@router.post("/login")
async def login(datos: LoginSchema):
    try:
        logger.info("=" * 50)
        logger.info("=== SOLICITUD DE LOGIN RECIBIDA ===")
        logger.info(f"Username: {datos.username}")
        logger.info(f"Password: {datos.password}")
        logger.info("=" * 50)
        
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
            
            logger.info(f"Usuario encontrado: {usuario}")
            
            if not usuario:
                logger.warning(f"Login fallido - Credenciales incorrectas para: {datos.username}")
                raise HTTPException(status_code=401, detail="Credenciales incorrectas")
            
            if usuario['estado'] != 'activo':
                logger.warning(f"Login fallido - Usuario inactivo: {datos.username}")
                raise HTTPException(status_code=401, detail="Usuario inactivo")
            
            # =========================================================
            # Si es TUTOR (rol=2)
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
            # Si es NIÑO (rol=3)
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
                
                # Calcular edad
                from datetime import date
                from controllers.ninos_controller import calcular_edad
                
                fecha_nac = nino['f_nac']
                if hasattr(fecha_nac, 'strftime'):
                    fecha_nac_str = fecha_nac.strftime('%Y-%m-%d')
                    edad = calcular_edad(fecha_nac)
                else:
                    fecha_nac_str = str(fecha_nac)
                    edad = calcular_edad(fecha_nac_str)
                
                return {
                    "status": "success",
                    "usuario": {
                        "id_user": usuario['id_user'],
                        "username": usuario['usr'],
                        "id_rol": 3,
                        "rol": "nino",
                        "id_nino": nino['id_nino'],
                        "nombre": nino['nombre'],
                        "f_nac": fecha_nac_str,
                        "edad": edad,
                        "genero": nino['genero'],
                        "escolaridad": nino['escolaridad'],
                        "tutor_id": nino['id_tut'],
                        "tutor_nombre": nino['tutor_nombre']
                    }
                }
            
            # =========================================================
            # Si es ADMIN (rol=1)
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
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/register")
async def register(datos: dict):
    try:
        logger.info(f"Registro de nuevo usuario: {datos}")
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Verificar si el username ya existe
            cursor.execute("SELECT id_user FROM usuario WHERE usr = %s", (datos.get('username'),))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
            
            # 1. Insertar en tabla 'usuario'
            query_user = "INSERT INTO usuario (usr, psw, id_rol, estado) VALUES (%s, %s, 2, 'activo')"
            cursor.execute(query_user, (datos.get('username'), datos.get('password')))
            id_nuevo_usuario = cursor.lastrowid

            # 2. Insertar en tabla 'tutor'
            query_tutor = """
                INSERT INTO tutor (id_user, nombre, email, celular, ocupacion, zona) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_tutor, (
                id_nuevo_usuario, 
                datos.get('nombre_completo'), 
                datos.get('email'), 
                datos.get('celular'), 
                datos.get('ocupacion'), 
                datos.get('zona')
            ))
            
            conn.commit()
            logger.info(f"Usuario registrado exitosamente: {datos.get('username')}")
            return {"status": "success", "username_generado": datos.get('username')}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno del servidor")