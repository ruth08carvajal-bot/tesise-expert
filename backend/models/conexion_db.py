import os
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "0")
        self.database = os.getenv("DB_NAME", "sis_expert_bd")
        self.conexion = None

    @contextmanager
    def obtener_conexion(self):
        """
        Generador de contexto para asegurar que la conexión y el cursor 
        se cierren siempre, pase lo que pase.
        """
        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                use_unicode=True,
                # SOLUCIÓN: Esto permite realizar múltiples consultas sin que se bloqueen
                get_warnings=True, 
                raise_on_warnings=True
            )
            yield self.conexion # Entrega la conexión al controlador
        except Error as e:
            print(f"Error crítico de base de datos: {e}")
            raise # Re-lanza el error para que el controlador sepa que falló
        finally:
            if self.conexion and self.conexion.is_connected():
                self.conexion.close()
                print("Conexión cerrada de forma segura por el gestor de contexto.")

db_admin = Database()