from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

# Configurar logging
from utils.logger import setup_logging
setup_logging()
from utils.logger import get_logger
logger = get_logger(__name__)

# --- IMPORTACIONES EXPLÍCITAS ---
from controllers.login_controller import router as login_router
from controllers.ninos_controller import router as ninos_router
from controllers.evaluacion_controller import router as evaluacion_router
from controllers.anamnesis_controller import router as anamnesis_router
from controllers.inferencia_controller import router as inferencia_router
from controllers.ejercicios_controller import router as ejercicios_router
from controllers.explicacion_controller import router as explicacion_router
from controllers.glosario_controller import router as glosario_router

app = FastAPI(
    title="Sistema Experto Fonoaudiológico - Tesis",
    description="Backend para la evaluación fonética-fonológica infantil usando MFCC y SE",
    version="1.0.0"
)

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Specific origins for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# =========================================================
# SERVIDOR DE ARCHIVOS ESTÁTICOS (imágenes, videos)
# =========================================================
# <--- CREA LA CARPETA 'static' en la raíz del backend --->
# <--- Dentro de 'static', crea: images/ y videos/ --->
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    logger.info(f"Creada carpeta estática en: {static_dir}")

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- REGISTRO DE RUTAS ---
app.include_router(login_router, prefix="/auth", tags=["Autenticación"])
app.include_router(ninos_router, prefix="/ninos", tags=["Gestión de Pacientes"])
app.include_router(evaluacion_router, prefix="/evaluacion", tags=["Motor de Inferencia"])
app.include_router(anamnesis_router, prefix="/anamnesis", tags=["Anamnesis"])
app.include_router(inferencia_router, prefix="/inferencia", tags=["Inferencia"])
app.include_router(ejercicios_router, prefix="/ejercicios", tags=["Ejercicios del Niño"])
app.include_router(explicacion_router, prefix="/explicacion", tags=["Módulo Explicativo"])
app.include_router(glosario_router, prefix="/glosario", tags=["Glosario"])


@app.get("/")
async def root():
    return {
        "mensaje": "Servidor del Sistema Experto Activo",
        "contexto": "La Paz, Bolivia",
        "estado": "Ready",
        "static_dir": static_dir
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=False)