from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from models.conexion_db import db_admin
from models.entidades import BaseReglas
from services.certeza_service import CertezaService
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ResultadoDiagnostico:
    """Estructura de resultado para cada diagnóstico."""
    id_diag: int
    nombre_diag: str
    fc_total: float
    explicacion: List[str] = field(default_factory=list)
    hechos_disparadores: List[int] = field(default_factory=list)
    reglas_aplicadas: List[str] = field(default_factory=list)
    confiabilidad: float = 0.0
    pasos_razonamiento: List[Dict] = field(default_factory=list)


class MotorInferencia:
    """
    Motor de inferencia con encadenamiento hacia atrás (backward chaining).
    """

    def __init__(self):
        self.trazas_actuales: List[str] = []
        self.hechos_disparadores: set = set()
        self.reglas_aplicadas: List[str] = []
        self.pasos_razonamiento: List[Dict] = []
        self.max_profundidad = 10

    # =========================================================
    # 1. BÚSQUEDA DE REGLAS
    # =========================================================
    
    def buscar_reglas_para_meta(self, id_diag: int) -> List[BaseReglas]:
        """
        Busca reglas simples que tienen como conclusión el diagnóstico.
        """
        reglas = []
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT id_regla, id_hecho, id_diag, peso_certeza, id_ejercicio_sugerido
                FROM base_reglas 
                WHERE id_diag = %s
            """, (id_diag,))
            for row in cursor.fetchall():
                reglas.append(BaseReglas(**row))
        return reglas

    def obtener_reglas_compuestas(self, id_diag: int) -> List[Tuple[Dict, List[Dict]]]:
        """
        Obtiene reglas compuestas (varias condiciones) para un diagnóstico.
        Retorna lista de (regla, detalles)
        """
        resultado = []
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT id_regla, id_diag, descripcion, umbral
                FROM reglas_compuestas 
                WHERE id_diag = %s
            """, (id_diag,))
            reglas = cursor.fetchall()

            for r in reglas:
                cursor.execute("""
                    SELECT id_detalle, id_regla, id_hecho, peso, operador, valor
                    FROM regla_detalle 
                    WHERE id_regla = %s
                """, (r['id_regla'],))
                detalles = cursor.fetchall()
                resultado.append((r, detalles))
        
        return resultado

    # =========================================================
    # 2. OBTENCIÓN DE CERTEZAS DE HECHOS
    # =========================================================
    
    def obtener_certeza_hecho(self, id_nino: int, id_ev: int, id_hecho: int, edad: int = None) -> float:
        """
        Calcula la certeza de un hecho específico.
        Fuentes: memoria_trabajo (evaluación actual) o anamnesis.
        """
        certeza = 0.0
        
        # 1. Buscar en memoria_trabajo (evaluación actual)
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT valor_obtenido, confiabilidad
                FROM memoria_trabajo 
                WHERE id_ev = %s AND id_hecho = %s
            """, (id_ev, id_hecho))
            res = cursor.fetchone()

            if res:
                certeza = float(res['valor_obtenido'])
                confiabilidad = float(res.get('confiabilidad', 1.0))
                certeza = certeza * confiabilidad
                logger.debug(f"Hecho H{id_hecho} en memoria: {certeza:.3f}")
        
        # 2. Si no hay en memoria, buscar en anamnesis
        if certeza == 0.0:
            certeza = self.obtener_certeza_anamnesis(id_nino, id_hecho)
            if certeza > 0:
                logger.debug(f"Hecho H{id_hecho} en anamnesis: {certeza:.3f}")
        
        # 3. Aplicar factor de edad
        if edad is not None and certeza > 0:
            factor = self.calcular_factor_edad(edad)
            certeza = certeza * factor
            logger.debug(f"Hecho H{id_hecho} con factor edad {edad}: {certeza:.3f}")
        
        return certeza

    def obtener_certeza_anamnesis(self, id_nino: int, id_hecho: int) -> float:
        """
        Obtiene certeza desde anamnesis_hechos.
        """
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT valor_presencia
                FROM anamnesis_hechos
                WHERE id_nino = %s AND id_hecho = %s
            """, (id_nino, id_hecho))
            row = cursor.fetchone()
            if row:
                valor = float(row['valor_presencia']) if row['valor_presencia'] else 1.0
                # La anamnesis tiene confiabilidad base de 0.8
                return valor * 0.8
            return 0.0

    def obtener_rendimiento_hecho(self, id_nino: int, id_hecho: int) -> float:
        """
        Obtiene el rendimiento histórico de un hecho.
        """
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT promedio FROM rendimiento_hecho
                WHERE id_nino = %s AND id_hecho = %s
            """, (id_nino, id_hecho))
            row = cursor.fetchone()
            return float(row['promedio']) if row else 0.0

    # =========================================================
    # 3. FACTORES DE EDAD (5-10 años)
    # =========================================================
    
    def calcular_factor_edad(self, edad: int) -> float:
        """
        Factor de corrección por edad para niños de 5 a 10 años.
        A mayor edad, MAYOR exigencia (factor más bajo,
        porque se espera mejor rendimiento).
        """
        if edad < 6:
            return 0.70   # 5 años: mucho margen
        elif edad < 7:
            return 0.80   # 6 años
        elif edad < 8:
            return 0.90   # 7 años
        elif edad < 9:
            return 0.95   # 8 años
        elif edad < 10:
            return 1.00   # 9 años: expectativa normal
        else:
            return 1.05   # 10 años: más exigente

    # =========================================================
    # 4. EVALUACIÓN DE REGLAS COMPUESTAS
    # =========================================================
    
    def evaluar_regla_compuesta(self, id_nino: int, id_ev: int, regla: Dict, detalles: List[Dict], edad: int = None) -> Tuple[float, List[str]]:
        """
        Evalúa una regla compuesta (AND entre múltiples condiciones).
        Retorna (certeza, lista de explicaciones)
        """
        explicaciones = []
        suma_ponderada = 0.0
        suma_pesos = 0.0
        condiciones_cumplidas = []
        
        for d in detalles:
            id_hecho = d['id_hecho']
            operador = d['operador']
            valor_umbral = d['valor']
            peso = d['peso']
            
            # Obtener certeza del hecho
            fc_hecho = self.obtener_certeza_hecho(id_nino, id_ev, id_hecho, edad)
            
            # Evaluar condición
            cumple = False
            if operador == '>':
                cumple = fc_hecho > valor_umbral
            elif operador == '<':
                cumple = fc_hecho < valor_umbral
            elif operador == '>=':
                cumple = fc_hecho >= valor_umbral
            elif operador == '<=':
                cumple = fc_hecho <= valor_umbral
            elif operador == '=':
                cumple = abs(fc_hecho - valor_umbral) < 0.01
            
            if cumple:
                suma_ponderada += fc_hecho * peso
                suma_pesos += peso
                condiciones_cumplidas.append(d)
                self.hechos_disparadores.add(id_hecho)
                explicaciones.append(f"   ✅ H{id_hecho}: {fc_hecho:.3f} {operador} {valor_umbral} (peso {peso})")
            else:
                explicaciones.append(f"   ❌ H{id_hecho}: {fc_hecho:.3f} {operador} {valor_umbral} → NO CUMPLE")
        
        if suma_pesos > 0:
            certeza_regla = suma_ponderada / suma_pesos
            umbral = regla.get('umbral', 0.5)
            
            if certeza_regla >= umbral:
                self.reglas_aplicadas.append(f"Regla compuesta {regla['id_regla']}")
                explicaciones.insert(0, f"✅ Regla compuesta {regla['id_regla']} activada (FC={certeza_regla:.3f} ≥ {umbral})")
                return certeza_regla, explicaciones
            else:
                explicaciones.insert(0, f"❌ Regla compuesta {regla['id_regla']} NO activada (FC={certeza_regla:.3f} < {umbral})")
                return 0.0, explicaciones
        
        return 0.0, explicaciones

    # =========================================================
    # 5. EVALUACIÓN DE REGLAS SIMPLES
    # =========================================================
    
    def evaluar_regla_simple(self, id_nino: int, id_ev: int, regla: BaseReglas, edad: int = None) -> Tuple[float, str]:
        """
        Evalúa una regla simple (hecho → diagnóstico).
        Retorna (certeza_propagar, explicacion)
        """
        id_hecho = regla.id_hecho
        peso = regla.peso_certeza
        
        # 1. Certeza actual (evaluación)
        fc_actual = self.obtener_certeza_hecho(id_nino, id_ev, id_hecho, edad)
        
        # 2. Certeza histórica (rendimiento)
        fc_hist = self.obtener_rendimiento_hecho(id_nino, id_hecho)
        
        # 3. Combinar: 70% actual, 30% histórico
        if fc_actual > 0 or fc_hist > 0:
            fc_hecho = (0.7 * fc_actual) + (0.3 * fc_hist)
        else:
            fc_hecho = 0.0
        
        # 4. Propagar a la conclusión
        fc_regla = CertezaService.propagar_condiciones([fc_hecho], peso)
        
        explicacion = f"H{id_hecho}: actual={fc_actual:.3f}, hist={fc_hist:.3f} → combinado={fc_hecho:.3f} → con peso={peso} → FC_regla={fc_regla:.3f}"
        
        return fc_regla, explicacion

    # =========================================================
    # 6. INFERENCIA PRINCIPAL (BACKWARD CHAINING)
    # =========================================================
    
    def inferir_backward(self, id_nino: int, id_ev: int, id_meta: int, edad: int = None, profundidad: int = 0) -> Tuple[float, List[str], List[int], List[str], List[Dict]]:
        """
        Encadenamiento hacia atrás.
        Retorna: (fc_total, explicaciones, hechos, reglas, pasos)
        """
        if profundidad > self.max_profundidad:
            logger.warning(f"Profundidad máxima alcanzada para diagnóstico {id_meta}")
            return 0.0, [], [], [], []
        
        # Inicializar para este diagnóstico
        self.trazas_actuales = []
        self.hechos_disparadores = set()
        self.reglas_aplicadas = []
        pasos = []
        
        fc_total = 0.0
        
        # =====================================================
        # PASO 1: Evaluar reglas compuestas
        # =====================================================
        reglas_compuestas = self.obtener_reglas_compuestas(id_meta)
        for regla, detalles in reglas_compuestas:
            fc_compuesta, explicacion = self.evaluar_regla_compuesta(id_nino, id_ev, regla, detalles, edad)
            
            if fc_compuesta > 0:
                pasos.append({
                    "tipo": "regla_compuesta",
                    "id_regla": regla['id_regla'],
                    "fc": round(fc_compuesta, 4),
                    "explicacion": explicacion
                })
                fc_total = CertezaService.combinar_mycin(fc_total, fc_compuesta)
                self.trazas_actuales.extend(explicacion)
        
        # =====================================================
        # PASO 2: Evaluar reglas simples
        # =====================================================
        reglas_simples = self.buscar_reglas_para_meta(id_meta)
        
        for regla in reglas_simples:
            fc_regla, explicacion = self.evaluar_regla_simple(id_nino, id_ev, regla, edad)
            
            if fc_regla > 0:
                # Combinar con total
                fc_total = CertezaService.combinar_mycin(fc_total, fc_regla)
                
                # Registrar
                self.hechos_disparadores.add(regla.id_hecho)
                regla_str = f"Regla H{regla.id_hecho} → D{id_meta} (peso={regla.peso_certeza})"
                self.reglas_aplicadas.append(regla_str)
                self.trazas_actuales.append(explicacion)
                
                pasos.append({
                    "tipo": "regla_simple",
                    "id_hecho": regla.id_hecho,
                    "peso": regla.peso_certeza,
                    "fc_hecho": fc_regla,
                    "explanation": explicacion
                })
                
                logger.debug(f"Regla simple: H{regla.id_hecho} → D{id_meta}: {fc_regla:.3f}")
        
        return fc_total, self.trazas_actuales, list(self.hechos_disparadores), self.reglas_aplicadas, pasos

    # =========================================================
    # 7. EJECUTAR DIAGNÓSTICO COMPLETO
    # =========================================================
    
    def ejecutar_diagnostico_completo(self, id_nino: int, id_ev: int, edad: int = None) -> List[ResultadoDiagnostico]:
        """
        Ejecuta diagnóstico para TODOS los diagnósticos posibles.
        Retorna lista de diagnósticos con certeza > 0.5, ordenados.
        """
        diagnosticos_finales: List[ResultadoDiagnostico] = []
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT id_diag, nombre_diag, categoria FROM catalogo_diagnosticos")
            catalogos = cursor.fetchall()

        for d in catalogos:
            id_diag = d['id_diag']
            nombre_diag = d['nombre_diag']
            
            logger.info(f"Evaluando diagnóstico: {nombre_diag} (ID {id_diag})")
            
            # Inferir para este diagnóstico
            fc_resultado, explicaciones, hechos, reglas, pasos = self.inferir_backward(
                id_nino, id_ev, id_diag, edad
            )
            
            if fc_resultado >= 0.5:
                logger.info(f"✅ {nombre_diag}: certeza {fc_resultado:.4f}")
                diagnosticos_finales.append(ResultadoDiagnostico(
                    id_diag=id_diag,
                    nombre_diag=nombre_diag,
                    fc_total=round(fc_resultado, 4),
                    explicacion=explicaciones,
                    hechos_disparadores=hechos,
                    reglas_aplicadas=reglas,
                    confiabilidad=round(fc_resultado, 4),
                    pasos_razonamiento=pasos
                ))
            else:
                logger.debug(f"❌ {nombre_diag}: certeza {fc_resultado:.4f} < 0.5")
        
        return sorted(diagnosticos_finales, key=lambda x: x.fc_total, reverse=True)

    # =========================================================
    # 8. MÉTODOS DE DEPURACIÓN (DEBUGGING)
    # =========================================================
    
    def evaluar_solo_reglas_compuestas(self, id_nino: int, id_ev: int, id_diag: int, edad: int = None) -> float:
        """
        Evalúa SOLO reglas compuestas para un diagnóstico.
        """
        reglas_compuestas = self.obtener_reglas_compuestas(id_diag)
        fc_total = 0.0
        
        for regla, detalles in reglas_compuestas:
            fc_compuesta, _ = self.evaluar_regla_compuesta(id_nino, id_ev, regla, detalles, edad)
            if fc_compuesta > 0:
                fc_total = CertezaService.combinar_mycin(fc_total, fc_compuesta)
        
        return fc_total

    def evaluar_solo_reglas_simples(self, id_nino: int, id_ev: int, id_diag: int, edad: int = None) -> float:
        """
        Evalúa SOLO reglas simples para un diagnóstico.
        """
        reglas = self.buscar_reglas_para_meta(id_diag)
        fc_total = 0.0
        
        for regla in reglas:
            fc_regla, _ = self.evaluar_regla_simple(id_nino, id_ev, regla, edad)
            if fc_regla > 0:
                fc_total = CertezaService.combinar_mycin(fc_total, fc_regla)
        
        return fc_total