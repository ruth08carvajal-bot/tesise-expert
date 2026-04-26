from typing import List, Dict
from models.conexion_db import db_admin

class ExplicacionService:
    @staticmethod
    def obtener_descripciones_hechos(ids_hechos: List[int]) -> Dict[int, str]:
        if not ids_hechos:
            return {}
        placeholders = ','.join(['%s'] * len(ids_hechos))
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT id_hecho, descripcion FROM base_hechos WHERE id_hecho IN ({placeholders})",
                ids_hechos
            )
            return {row['id_hecho']: row['descripcion'] for row in cursor.fetchall()}

    @staticmethod
    def generar_texto_diagnostico(nombre_diag: str, fc_total: float, hechos: List[int], reglas: List[str]) -> str:
        texto = [
            f"El diagnóstico sugerido es {nombre_diag} con una confiabilidad de {(fc_total * 100):.1f}%.",
            "Se determinó a partir de la combinación de evidencia clínica y los resultados de las pruebas realizadas."
        ]

        if hechos:
            hechos_texto = ', '.join([f'H{hid}' for hid in hechos])
            texto.append(f"Los hechos disparadores que respaldan este diagnóstico son: {hechos_texto}.")

        if reglas:
            reglas_texto = ', '.join(reglas)
            texto.append(f"Se aplicaron las siguientes reglas de inferencia: {reglas_texto}.")

        texto.append("La evidencia ha sido ponderada con la confiabilidad de cada prueba para asegurar una recomendación clínica robusta.")
        return ' '.join(texto)

    @staticmethod
    def generar_texto_ejercicios(plan: List[Dict]) -> str:
        if not plan:
            return "No se encontró un plan de ejercicios disponible en este momento."

        ejercicios = [f"{item['nombre_ejercicio']} ({item['nivel_dificultad']})" for item in plan[:5]]
        texto = (
            "El sistema recomienda los siguientes ejercicios porque están alineados con los patrones de error detectados y el nivel de desarrollo del niño: "
            + ', '.join(ejercicios) + "."
        )
        texto += " Estos ejercicios fueron seleccionados para reforzar las áreas con menor desempeño y promover un avance gradual en la pronunciación y comprensión."
        return texto

    @staticmethod
    def generar_resumen_general(diagnosticos: List[Dict], plan: List[Dict], anamnesis: List[Dict], mfcc_scores: List[Dict]) -> str:
        partes = []
        if anamnesis:
            partes.append("La anamnesis identificó antecedentes relevantes que contribuyen a la interpretación clínica.")
        if mfcc_scores:
            partes.append("Las puntuaciones MFCC reflejan la similitud acústica entre la producción del niño y los patrones esperados.")
        if diagnosticos:
            partes.append("Se priorizaron los diagnósticos con mayor certeza para entregar una recomendación precisa.")
        if plan:
            partes.append("El plan de ejercicios combina apoyo auditivo y articulatorio para mejorar las habilidades fonológicas.")

        if not partes:
            return "No se encontró información suficiente para generar un resumen clínico."

        return ' '.join(partes)

    @staticmethod
    def preguntas_frecuentes() -> List[Dict[str, str]]:
        return [
            {
                'pregunta': '¿Por qué recibo varios diagnósticos?',
                'respuesta': 'El sistema identifica múltiples áreas de riesgo. Cada diagnóstico se muestra solo si alcanza al menos 50% de certeza.'
            },
            {
                'pregunta': '¿Qué significa la confiabilidad mostrada?',
                'respuesta': 'La confiabilidad indica qué tan sólida es la evidencia calculada con base en el audio, la anamnesis y el historial de desempeño.'
            },
            {
                'pregunta': '¿Por qué se recomiendan estos ejercicios?',
                'respuesta': 'Los ejercicios se eligen según las reglas clínicas que relacionan los hechos detectados con las necesidades de intervención del niño.'
            },
            {
                'pregunta': '¿Puedo compartir este informe con otros profesionales?',
                'respuesta': 'Sí. El PDF clínico incluye anamnesis, evaluación MFCC, diagnósticos y plan de ejercicios para facilitar la comunicación con especialistas.'
            }
        ]

    @staticmethod
    def formatear_parrafo(texto: str, ancho: int = 90) -> str:
        palabras = texto.split()
        lineas = []
        linea_actual = ''
        for palabra in palabras:
            if len(linea_actual) + len(palabra) + 1 > ancho:
                lineas.append(linea_actual.strip())
                linea_actual = palabra + ' '
            else:
                linea_actual += palabra + ' '
        if linea_actual:
            lineas.append(linea_actual.strip())
        return '\n'.join(lineas)

