class LogicaDifusaService:
    @staticmethod
    def obtener_etiqueta(valor_0_1: float) -> str:
        # Convertimos a porcentaje para las funciones del ejemplo
        x = valor_0_1 * 100
        
        if x < 40: return "Dificultad Severa (Bajo)"
        if x < 75: return "Dificultad Leve (Medio)"
        return "Producción Correcta (Alto)"