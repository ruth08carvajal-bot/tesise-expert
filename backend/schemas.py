from pydantic import BaseModel, Field, validator
from typing import Optional

class LoginSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)  # Note: password validation, but not touching as per user request

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('.', '').replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric with . or _')
        return v

class NinoSchema(BaseModel):
    id_tut: int = Field(..., gt=0)
    nombre: str = Field(..., min_length=1, max_length=100)
    f_nac: str  # Date in YYYY-MM-DD format
    genero: str = Field(..., min_length=1, max_length=1)  # M o F
    escolaridad: str = Field(..., min_length=1)
    parentesco: str = Field(..., min_length=1)

class NinoUpdateSchema(BaseModel):
    nombre: str
    f_nac: str
    genero: str
    escolaridad: str
    parentesco: str

    class Config:
        extra = 'ignore'  # Ignorar campos adicionales

class AnamnesisSchema(BaseModel):
    id_nino: int = Field(..., gt=0)
    respuestas: dict  # JSON object with answers

class EvaluacionManual(BaseModel):
    id_nino: int = Field(..., gt=0)
    id_evaluacion: int = Field(..., gt=0)
    id_hecho: int = Field(..., gt=0)
    valor: float = Field(..., ge=0.0, le=1.0)

class GuardarProgresoSchema(BaseModel):
    id_nino: int = Field(..., gt=0)
    id_ejercicio: int = Field(..., gt=0)
    puntaje_obtenido: float = Field(..., ge=0.0, le=1.0)
    tiempo_empleado: int = Field(..., ge=0)