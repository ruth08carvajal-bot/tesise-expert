from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CAMBIO AQUÍ: Importaciones explícitas ---
from controllers.login_controller import router as login_router
from controllers.ninos_controller import router as ninos_router
from controllers.evaluacion_controller import router as evaluacion_router
from controllers.anamnesis_controller import router as anamnesis_router
from controllers.inferencia_controller import router as inferencia_router
from controllers.ejercicios_controller import router as ejercicios_router

app = FastAPI(
    title="Sistema Experto Fonoaudiológico - Tesis",
    description="Backend para la evaluación fonética-fonológica infantil usando MFCC y SE",
    version="1.0.0"
)

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DE RUTAS (Usando los nuevos alias) ---
app.include_router(login_router, prefix="/auth", tags=["Autenticación"])
app.include_router(ninos_router, prefix="/ninos", tags=["Gestión de Pacientes"])
app.include_router(evaluacion_router, prefix="/evaluacion", tags=["Motor de Inferencia"])
app.include_router(anamnesis_router, prefix="/anamnesis", tags=["Anamnesis"])
app.include_router(inferencia_router, prefix="/inferencia", tags=["Inferencia"])
app.include_router(ejercicios_router, prefix="/ejercicios", tags=["Ejercicios del Niño"])

@app.get("/")
async def root():
    return {
        "mensaje": "Servidor del Sistema Experto Activo",
        "contexto": "La Paz, Bolivia",
        "estado": "Ready"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=False)