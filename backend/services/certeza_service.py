import numpy as np

class CertezaService:
    """
    Implementación de las ecuaciones del Marco Teórico (Capítulo II).
    """

    @staticmethod
    def combinar_mycin(fc1: float, fc2: float) -> float:
        """
        Ec. 2.7 (MYCIN): Combinación de certezas de diferentes reglas
        para una misma conclusión.
        """
        # FC_combinado = FC1 + FC2 * (1 - FC1)
        return fc1 + fc2 * (1 - fc1)

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