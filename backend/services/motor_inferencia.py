from typing import Dict, List, Optional
from dataclasses import dataclass
from models.conexion_db import db_admin
from models.entidades import BaseReglas
from services.certeza_service import CertezaService

@dataclass
class ResultadoDiagnostico:
    id_diag: int
    nombre_diag: str
    fc_total: float
    explicacion: List[str]

class MotorInferencia:
    def __init__(self):
        self.trazas_actuales = []

    def buscar_reglas_para_meta(self, id_diag: int) -> List[BaseReglas]:
        reglas = []
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM base_reglas WHERE id_diag = %s", (id_diag,))
            for row in cursor.fetchall():
                reglas.append(BaseReglas(**row))
        return reglas

    def obtener_certeza_hecho(self, id_nino: int, id_ev: int, id_hecho: int) -> float:
        """
        BUSCADOR INTELIGENTE DE EVIDENCIA:
        Busca si el hecho viene de la Anamnesis o de la Evaluación (MFCC/Ejercicios).
        """
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # 1. Verificar el origen del hecho
            cursor.execute("SELECT instrumento_origen FROM base_hechos WHERE id_hecho = %s", (id_hecho,))
            info_hecho = cursor.fetchone()
            
            if not info_hecho:
                return 0.0

            origen = info_hecho['instrumento_origen']

            # 2. Hechos provenientes del entorno familiar/anamnesis
            if origen in ['Tutor', 'Social']:
                cursor.execute(
                    "SELECT 1.0 as valor FROM anamnesis_hechos WHERE id_nino = %s AND id_hecho = %s",
                    (id_nino, id_hecho)
                )
                res = cursor.fetchone()
                return float(res['valor']) if res else 0.0

            # 3. Hechos provenientes de la evaluación técnica (MFCC, TAR, etc.)
            else:
                cursor.execute(
                    "SELECT valor_obtenido FROM memoria_trabajo WHERE id_ev = %s AND id_hecho = %s",
                    (id_ev, id_hecho)
                )
                res = cursor.fetchone()
                return float(res['valor_obtenido']) if res else 0.0

    def inferir_backward(self, id_nino: int, id_ev: int, id_meta: int) -> float:
        """
        IMPLEMENTACIÓN DE ENCADENAMIENTO HACIA ATRÁS (BACKWARD CHAINING).
        Integración de contexto Anamnesis + Evaluación Directa.
        """
        reglas = self.buscar_reglas_para_meta(id_meta)
        fc_acumulado = 0.0

        for regla in reglas:
            fc_hecho = self.obtener_certeza_hecho(id_nino, id_ev, regla.id_hecho)

            if fc_hecho > 0:
                # Propagación (Ec. 2.8)
                fc_concl_regla = CertezaService.propagar_condiciones(
                    [fc_hecho], 
                    regla.weight_certeza if hasattr(regla, 'weight_certeza') else regla.peso_certeza
                )
                
                # Combinación MYCIN (Ec. 2.7)
                fc_viejo = fc_acumulado
                fc_acumulado = CertezaService.combinar_mycin(fc_viejo, fc_concl_regla)
                
                self.trazas_actuales.append(
                    f"Hecho H{regla.id_hecho} confirmado (FC={fc_hecho:.2f}). "
                    f"Certeza combinada: {fc_acumulado:.4f}"
                )

        return fc_acumulado

    def ejecutar_diagnostico_completo(self, id_nino: int, id_ev: int) -> List[ResultadoDiagnostico]:
        diagnosticos_finales = []
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT id_diag, nombre_diag FROM catalogo_diagnosticos")
            catalogos = cursor.fetchall()

        for d in catalogos:
            self.trazas_actuales = [] 
            fc_resultado = self.inferir_backward(id_nino, id_ev, d['id_diag'])

            if fc_resultado > 0.1: # Umbral mínimo para mostrar diagnóstico
                diagnosticos_finales.append(ResultadoDiagnostico(
                    id_diag=d['id_diag'],
                    nombre_diag=d['nombre_diag'],
                    fc_total=round(fc_resultado, 4),
                    explicacion=list(self.trazas_actuales)
                ))

        # Ordenar por mayor certeza
        return sorted(diagnosticos_finales, key=lambda x: x.fc_total, reverse=True)