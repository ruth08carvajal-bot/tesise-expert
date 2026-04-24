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
    # nuevo metodo de reglas compuestas 23/04/26
    def obtener_reglas_compuestas(self, id_diag: int):
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("SELECT * FROM reglas_compuestas WHERE id_diag = %s", (id_diag,))
            reglas = cursor.fetchall()

            resultado = []
            for r in reglas:
                cursor.execute("SELECT * FROM regla_detalle WHERE id_regla = %s", (r['id_regla'],))
                detalles = cursor.fetchall()
                resultado.append((r, detalles))

            return resultado
    def evaluar_regla_compuesta(self, id_nino, id_ev, regla, detalles):
        suma = 0.0

        for d in detalles:
            valor_hecho = self.obtener_certeza_hecho(id_nino, id_ev, d['id_hecho'])

            cumple = False
            if d['operador'] == '>':
                cumple = valor_hecho > d['valor']
            elif d['operador'] == '<':
                cumple = valor_hecho < d['valor']
            elif d['operador'] == '=':
                cumple = valor_hecho == d['valor']

            if cumple:
                suma += d['peso'] * valor_hecho

        return suma
    # nueva función 23/04/26 para obtener certeza de un hecho específico considerando confiabilidad
    def obtener_certeza_hecho(self, id_nino: int, id_ev: int, id_hecho: int) -> float:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)

            cursor.execute("""
                SELECT valor_obtenido, confiabilidad
                FROM memoria_trabajo 
                WHERE id_ev = %s AND id_hecho = %s
            """, (id_ev, id_hecho))

            res = cursor.fetchone()
            if res:
                valor = float(res['valor_obtenido'])
                confiabilidad = float(res.get('confiabilidad', 1.0))
                return valor * confiabilidad
            return 0.0
    #nueva funcion 23/04/26 para obtener rendimiento histórico de un hecho específico
    def obtener_rendimiento_hecho(self, id_nino: int, id_hecho: int) -> float:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT promedio FROM rendimiento_hecho
                WHERE id_nino = %s AND id_hecho = %s
            """, (id_nino, id_hecho))
            row = cursor.fetchone()
            return float(row['promedio']) if row else 0.0

   
    # nueva función de inferencia con integración total de reglas compuestas y ajuste por confiabilidad 23/04/26
    def inferir_backward(self, id_nino: int, id_ev: int, id_meta: int) -> float:
        fc_total = 0.0

        # ============================================
        # 1. REGLAS COMPUESTAS (nivel clínico experto)
        # ============================================
        reglas_compuestas = self.obtener_reglas_compuestas(id_meta)

        for regla, detalles in reglas_compuestas:
            fc_compuesta = self.evaluar_regla_compuesta(id_nino, id_ev, regla, detalles)

            if fc_compuesta >= regla['umbral']:
                self.trazas_actuales.append(
                    f"Regla compuesta activada → FC={fc_compuesta:.2f} (umbral={regla['umbral']})"
                )

                fc_total = CertezaService.combinar_mycin(fc_total, fc_compuesta)

        # ============================================
        # 2. REGLAS CLÁSICAS (MYCIN)
        # ============================================
        reglas = self.buscar_reglas_para_meta(id_meta)

        for regla in reglas:
            fc_actual = self.obtener_certeza_hecho(id_nino, id_ev, regla.id_hecho)
            fc_hist = self.obtener_rendimiento_hecho(id_nino, regla.id_hecho)

            # 🔥 COMBINACIÓN ADAPTATIVA (historial + actual)
            fc_hecho = (0.7 * fc_actual) + (0.3 * fc_hist)

            # 🔥 AJUSTE POR CONFIABILIDAD (nuevo)
            confiabilidad = self.obtener_confiabilidad(id_ev, regla.id_hecho)
            fc_hecho = fc_hecho * confiabilidad

            if fc_hecho > 0:
                fc_regla = CertezaService.propagar_condiciones(
                    [fc_hecho],
                    regla.peso_certeza
                )

                fc_total = CertezaService.combinar_mycin(fc_total, fc_regla)

                self.trazas_actuales.append(
                    f"Hecho H{regla.id_hecho} → FC={fc_hecho:.2f} (conf={confiabilidad}) → Total={fc_total:.4f}"
                )

        return fc_total

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
    # nueva función 23/04/26 para evaluar reglas compuestas de un diagnóstico específico
    def evaluar_reglas_compuestas(self, id_nino: int, id_ev: int, id_diag: int) -> float:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)

            # Obtener reglas compuestas del diagnóstico
            cursor.execute("""
                SELECT * FROM reglas_compuestas 
                WHERE id_diag = %s
            """, (id_diag,))
            reglas = cursor.fetchall()

            fc_total = 0.0

            for regla in reglas:
                id_regla = regla['id_regla']
                umbral = regla['umbral']

                # Obtener condiciones
                cursor.execute("""
                    SELECT * FROM regla_detalle 
                    WHERE id_regla = %s
                """, (id_regla,))
                detalles = cursor.fetchall()

                suma_ponderada = 0.0
                suma_pesos = 0.0

                for d in detalles:
                    fc = self.obtener_certeza_hecho(id_nino, id_ev, d['id_hecho'])

                    # Evaluación de operador
                    cumple = False
                    if d['operador'] == '>':
                        cumple = fc > d['valor']
                    elif d['operador'] == '<':
                        cumple = fc < d['valor']
                    elif d['operador'] == '=':
                        cumple = fc == d['valor']

                    if cumple:
                        suma_ponderada += fc * d['peso']
                        suma_pesos += d['peso']

                if suma_pesos > 0:
                    fc_regla = suma_ponderada / suma_pesos

                    if fc_regla >= umbral:
                        fc_total = CertezaService.combinar_mycin(fc_total, fc_regla)

                        self.trazas_actuales.append(
                            f"[COMPUESTA] Regla {id_regla} activada (FC={fc_regla:.3f})"
                        )

            return fc_total
    # nueva función 23/04/26 para obtener confiabilidad de un hecho específico en una evaluación
    def obtener_confiabilidad(self, id_ev, id_hecho):
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT confiabilidad FROM memoria_trabajo
                WHERE id_ev=%s AND id_hecho=%s
            """, (id_ev, id_hecho))

            row = cursor.fetchone()
            return float(row['confiabilidad']) if row else 1.0