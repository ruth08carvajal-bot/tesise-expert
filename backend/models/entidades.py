from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# --- SEGURIDAD Y USUARIOS ---

class Rol(BaseModel):
    id_rol: int
    nombre: str

class Usuario(BaseModel):
    id_user: Optional[int] = None
    usr: str
    psw: str
    id_rol: int
    estado: str = "activo"
    fecha_reg: Optional[datetime] = None

class Admin(BaseModel):
    id_adm: Optional[int] = None
    id_user: int
    nombre: str
    cargo: str

class Tutor(BaseModel):
    id_tut: Optional[int] = None
    id_user: int
    nombre: str
    email: Optional[str] = None
    celular: Optional[str] = None
    ocupacion: Optional[str] = None
    zona: Optional[str] = None

class Nino(BaseModel):
    id_nino: Optional[int] = None
    id_user: int
    id_tut: int
    nombre: str
    f_nac: date
    genero: Optional[str] = None
    escolaridad: Optional[str] = None
    parentesco: Optional[str] = None

# --- BASE DE CONOCIMIENTO (ESTÁTICA) ---

class BaseHechos(BaseModel):
    id_hecho: int
    cod_h: str
    descripcion: str
    categoria_clinica: Optional[str] = None
    instrumento_origen: Optional[str] = None

class CatalogoDiagnosticos(BaseModel):
    id_diag: int
    nombre_diag: str
    definicion_sencilla: Optional[str] = None
    categoria: Optional[str] = None

class CatalogoEjercicios(BaseModel):
    id_ejercicio: int
    nombre_ejercicio: str
    descripcion_instrucciones: Optional[str] = None
    nivel_dificultad: str # Bajo, Medio, Alto
    tipo_apoyo: Optional[str] = None
    id_hecho_objetivo: Optional[int] = None

class BaseReglas(BaseModel):
    id_regla: Optional[int] = None
    id_hecho: int
    id_diag: int
    id_ejercicio_sugerido: Optional[int] = None
    peso_certeza: float

# --- PROCESO CLÍNICO Y EVALUACIÓN (DINÁMICA) ---

class FichaAntecedentes(BaseModel):
    id_nino: int
    historia_clinica: Optional[str] = None

class AnamnesisHechos(BaseModel):
    id_ana_h: Optional[int] = None
    id_nino: int
    id_hecho: int
    valor_presencia: int = 1

class EvaluacionSesion(BaseModel):
    id_ev: Optional[int] = None
    id_nino: int
    fecha_eval: Optional[datetime] = None
    diagnostico_sistema: Optional[str] = None
    pronostico_sistema: Optional[str] = None
    sugerencia_ejercicios: Optional[str] = None
    explicacion_logica: Optional[str] = None
    notas_tutor: Optional[str] = None
    tipo_evaluacion: str = "Control"

class MemoriaTrabajo(BaseModel):
    id_mem: Optional[int] = None
    id_ev: int
    id_hecho: int
    valor_obtenido: float

class ProgresoNino(BaseModel):
    id_progreso: Optional[int] = None
    id_nino: int
    id_ejercicio: int
    fecha_realizacion: Optional[datetime] = None
    puntaje_obtenido: float
    tiempo_empleado: int
    intento_numero: int
    progreso_alcanzado: int = 0
    estado_actual: str = "iniciado"