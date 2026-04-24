from fastapi import APIRouter, HTTPException
from services.motor_inferencia import MotorInferencia
from models.conexion_db import db_admin

router = APIRouter()
motor = MotorInferencia()

def obtener_id_nino_por_evaluacion(id_ev: int):
    with db_admin.obtener_conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_nino FROM evaluacion_sesion WHERE id_ev = %s",
            (id_ev,)
        )
        row = cursor.fetchone()
        return row['id_nino'] if row else None

@router.post("/procesar_diagnostico/{id_ev}")
async def procesar_diagnostico(id_ev: int):
    """
    Este endpoint es el que llamarás desde Android (Kotlin).
    """
    try:
        id_nino = obtener_id_nino_por_evaluacion(id_ev)
        if id_nino is None:
            raise HTTPException(status_code=404, detail=f"Evaluación {id_ev} no encontrada")

        resultado = motor.ejecutar_diagnostico_completo(id_nino, id_ev)
        if not resultado:
            return {"status": "success", "data": [], "mensaje": "No hay suficiente evidencia."}
        return {"status": "success", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))