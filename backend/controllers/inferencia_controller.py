from fastapi import APIRouter, HTTPException
from services.motor_inferencia import MotorInferencia

router = APIRouter()
motor = MotorInferencia()

@router.post("/procesar_diagnostico/{id_ev}")
async def procesar_diagnostico(id_ev: int):
    """
    Este endpoint es el que llamarás desde Android (Kotlin).
    """
    try:
        resultado = motor.ejecutar_diagnostico_completo(id_ev)
        if not resultado:
            return {"status": "success", "data": [], "mensaje": "No hay suficiente evidencia."}
        return {"status": "success", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))