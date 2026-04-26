from typing import Dict, List, Optional
from dataclasses import dataclass, field
from models.conexion_db import db_admin
from models.entidades import BaseReglas
from services.certeza_service import CertezaService

@dataclass
class ResultadoDiagnostico:
    id_diag: int
    nombre_diag: str
    fc_total: float
    explicacion: List[str] = field(default_factory=list)
    hechos_disparadores: List[int] = field(default_factory=list)
    reglas_aplicadas: List[str] = field(default_factory=list)
    confiabilidad: float = 0.0

class MotorInferencia:
    def __init__(self):
        self.trazas_actuales: List[str] = []
        self.hechos_disparadores: set = set()
        self.reglas_aplicadas: List[str] = []

    def buscar_reglas_para_meta(self, id_diag: int) -> List[BaseReglas]:
        reglas = []
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM base_reglas WHERE id_diag = %s", (id_diag,))
            for row in cursor.fetchall():
                reglas.append(BaseReglas(**row))
        return reglas

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

    def evaluar_regla_compuesta(self, id_nino: int, id_ev: int, regla, detalles, edad: int = None):
        suma = 0.0

        for d in detalles:
            valor_hecho = self.obtener_certeza_hecho(id_nino, id_ev, d['id_hecho'], edad)

            cumple = False
            if d['operador'] == '>':
                cumple = valor_hecho > d['valor']
            elif d['operador'] == '<':
                cumple = valor_hecho < d['valor']
            elif d['operador'] == '=':
                cumple = valor_hecho == d['valor']

            if cumple:
                suma += d['peso'] * valor_hecho
                self.hechos_disparadores.add(d['id_hecho'])

        return suma

    def obtener_certeza_anamnesis(self, id_nino: int, id_hecho: int) -> float:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT valor_presencia
                FROM anamnesis_hechos
                WHERE id_nino = %s AND id_hecho = %s
            """, (id_nino, id_hecho))
            row = cursor.fetchone()
            if row:
                try:
                    valor_presencia = float(row['valor_presencia'])
                except (TypeError, ValueError):
                    valor_presencia = 1.0
                return valor_presencia * 0.9
            return 0.0

    def calcular_factor_edad(self, edad: int) -> float:
        if edad < 4:
            return 0.7
        elif edad < 6:
            return 0.85
        elif edad < 8:
            return 0.95
        return 1.0

    def obtener_certeza_hecho(self, id_nino: int, id_ev: int, id_hecho: int, edad: int = None) -> float:
        if isinstance(id_hecho, str) and id_hecho.isdigit():
            id_hecho = int(id_hecho)

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
                certeza = valor * confiabilidad
            else:
                certeza = 0.0

        if certeza == 0.0:
            certeza = self.obtener_certeza_anamnesis(id_nino, id_hecho)

        if edad is not None:
            certeza *= self.calcular_factor_edad(edad)

        return certeza

    def obtener_rendimiento_hecho(self, id_nino: int, id_hecho: int) -> float:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT promedio FROM rendimiento_hecho
                WHERE id_nino = %s AND id_hecho = %s
            """, (id_nino, id_hecho))
            row = cursor.fetchone()
            return float(row['promedio']) if row else 0.0

    def inferir_backward(self, id_nino: int, id_ev: int, id_meta: int, edad: int = None) -> float:
        self.trazas_actuales = []
        self.hechos_disparadores = set()
        self.reglas_aplicadas = []
        fc_total = 0.0

        reglas_compuestas = self.obtener_reglas_compuestas(id_meta)
        for regla, detalles in reglas_compuestas:
            fc_compuesta = self.evaluar_regla_compuesta(id_nino, id_ev, regla, detalles, edad)
            if fc_compuesta >= regla['umbral']:
                self.reglas_aplicadas.append(f"Regla compuesta {regla['id_regla']}")
                self.trazas_actuales.append(
                    f"Regla compuesta activada → FC={fc_compuesta:.2f} (umbral={regla['umbral']})"
                )
                fc_total = CertezaService.combinar_mycin(fc_total, fc_compuesta)

        reglas = self.buscar_reglas_para_meta(id_meta)
        for regla in reglas:
            fc_actual = self.obtener_certeza_hecho(id_nino, id_ev, regla.id_hecho, edad)
            fc_hist = self.obtener_rendimiento_hecho(id_nino, regla.id_hecho)
            fc_hecho = (0.7 * fc_actual) + (0.3 * fc_hist)
            confiabilidad = self.obtener_confiabilidad(id_ev, regla.id_hecho)
            fc_hecho = fc_hecho * confiabilidad

            if fc_hecho > 0:
                fc_regla = CertezaService.propagar_condiciones([
                    fc_hecho
                ], regla.peso_certeza)
                fc_total = CertezaService.combinar_mycin(fc_total, fc_regla)
                self.hechos_disparadores.add(regla.id_hecho)
                self.reglas_aplicadas.append(f"Regla clásica H{regla.id_hecho} → D{regla.id_diag}")
                self.trazas_actuales.append(
                    f"Hecho H{regla.id_hecho} → FC={fc_hecho:.2f} (conf={confiabilidad}) → Total={fc_total:.4f}"
                )

        return fc_total

    def ejecutar_diagnostico_completo(self, id_nino: int, id_ev: int, edad: int = None) -> List[ResultadoDiagnostico]:
        diagnosticos_finales: List[ResultadoDiagnostico] = []
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT id_diag, nombre_diag FROM catalogo_diagnosticos")
            catalogos = cursor.fetchall()

        for d in catalogos:
            fc_resultado = self.inferir_backward(id_nino, id_ev, d['id_diag'], edad)
            if fc_resultado >= 0.5:
                diagnosticos_finales.append(ResultadoDiagnostico(
                    id_diag=d['id_diag'],
                    nombre_diag=d['nombre_diag'],
                    fc_total=round(fc_resultado, 4),
                    explicacion=list(self.trazas_actuales),
                    hechos_disparadores=list(self.hechos_disparadores),
                    reglas_aplicadas=list(dict.fromkeys(self.reglas_aplicadas)),
                    confiabilidad=round(fc_resultado, 4)
                ))

        return sorted(diagnosticos_finales, key=lambda x: x.fc_total, reverse=True)

    def evaluar_reglas_compuestas(self, id_nino: int, id_ev: int, id_diag: int) -> float:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM reglas_compuestas 
                WHERE id_diag = %s
            """, (id_diag,))
            reglas = cursor.fetchall()

            fc_total = 0.0
            for regla in reglas:
                id_regla = regla['id_regla']
                umbral = regla['umbral']
                cursor.execute("""
                    SELECT * FROM regla_detalle 
                    WHERE id_regla = %s
                """, (id_regla,))
                detalles = cursor.fetchall()

                suma_ponderada = 0.0
                suma_pesos = 0.0
                for d in detalles:
                    fc = self.obtener_certeza_hecho(id_nino, id_ev, d['id_hecho'], edad)
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
                        self.hechos_disparadores.add(d['id_hecho'])

                if suma_pesos > 0:
                    fc_regla = suma_ponderada / suma_pesos
                    if fc_regla >= umbral:
                        fc_total = CertezaService.combinar_mycin(fc_total, fc_regla)
                        self.reglas_aplicadas.append(f"Regla compuesta {id_regla}")
                        self.trazas_actuales.append(
                            f"[COMPUESTA] Regla {id_regla} activada (FC={fc_regla:.3f})"
                        )

            return fc_total

    def obtener_confiabilidad(self, id_ev, id_hecho):
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT confiabilidad FROM memoria_trabajo
                WHERE id_ev=%s AND id_hecho=%s
            """, (id_ev, id_hecho))
            row = cursor.fetchone()
            return float(row['confiabilidad']) if row else 1.0