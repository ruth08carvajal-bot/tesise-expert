import numpy as np

class CertezaService:
    """
    Implementación de las ecuaciones del Marco Teórico (Capítulo II).
    """

    @staticmethod
    def combinar_mycin(fc1: float, fc2: float) -> float:
        """
        Ec. 2.7 (MYCIN):Combina dos factores de certeza de la misma conclusión.
        Fórmula MYCIN: CFcomb = CF1 + CF2 * (1 - CF1)
        """
        if fc1 == 0 and fc2 == 0:
            return 0.0
        
        # Ambos positivos
        if fc1 >= 0 and fc2 >= 0:
            return fc1 + fc2 * (1 - fc1)
        
        # Ambos negativos
        if fc1 <= 0 and fc2 <= 0:
            return fc1 + fc2 * (1 + fc1)
        
        # Diferentes signos
        return (fc1 + fc2) / (1 - min(abs(fc1), abs(fc2)))

    @staticmethod
    def propagar_condiciones(lista_fc_condiciones: list[float], fc_regla: float) -> float:
        """
        Ec. 2.8 (Propagación): Para reglas con múltiples condiciones.
        FC_conclusion = min(FC_cond1, FC_cond2, ..., FC_condN) * FC_regla
        """
        if not lista_fc_condiciones:
            return 0.0
        
        # Tomamos el valor mínimo de las condiciones (el eslabón más débil)
        fc_minimo = min(lista_fc_condiciones)
        
        # Multiplicamos por el peso o factor de la regla
        return fc_minimo * fc_regla