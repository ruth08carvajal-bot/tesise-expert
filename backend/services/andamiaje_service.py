from models.conexion_db import db_admin

class AndamiajeService:
    """
    Implementa el algoritmo de ajuste de dificultad basado en el 
    desempeño histórico del niño (Zona de Desarrollo Próximo).
    """
    UMBRAL_SUBIR = 70.0 # Si supera el 70% de precisión, sube de nivel
    UMBRAL_BAJAR = 40.0 # Si baja del 40%, necesita más apoyo

    @staticmethod
    def calcular_nivel_nuevo(precision_promedio: float, nivel_actual: str) -> str:
        escalera = {
            'Bajo':  {'subir': 'Medio', 'bajar': 'Bajo'},
            'Medio': {'subir': 'Alto',  'bajar': 'Bajo'},
            'Alto':  {'subir': 'Alto',  'bajar': 'Medio'}
        }
        
        if precision_promedio >= AndamiajeService.UMBRAL_SUBIR:
            return escalera[nivel_actual]['subir']
        elif precision_promedio <= AndamiajeService.UMBRAL_BAJAR:
            return escalera[nivel_actual]['bajar']
        return nivel_actual

    def obtener_progreso_reciente(self, id_nino: int, id_ejercicio: int):
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
                SELECT AVG(puntaje_obtenido) FROM progreso_nino 
                WHERE id_nino = %s AND id_ejercicio = %s
                ORDER BY fecha_realizacion DESC LIMIT 5
            """
            cursor.execute(query, (id_nino, id_ejercicio))
            res = cursor.fetchone()
            return float(res[0]) if res[0] else 0.0