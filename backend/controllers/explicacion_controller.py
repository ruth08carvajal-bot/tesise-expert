from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from models.conexion_db import db_admin
from services.motor_inferencia import MotorInferencia
from services.explicacion_service import ExplicacionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
motor = MotorInferencia()
explicacion_service = ExplicacionService()


class PreguntaExplicacion(BaseModel):
    id_nino: int
    id_evaluacion: int
    pregunta: str


@router.post("/explicar")
async def explicar_diagnostico(datos: PreguntaExplicacion):
    """
    Endpoint para el módulo explicativo.
    Responde preguntas del tutor sobre diagnósticos, ejercicios y resultados.
    """
    try:
        from controllers.evaluacion_controller import obtener_informe_clinico
        
        informe = obtener_informe_clinico(datos.id_nino, datos.id_evaluacion)
        
        pregunta = datos.pregunta.lower()
        
        # Detectar tipo de pregunta
        if any(p in pregunta for p in ["diagnóstico", "diagnostico", "tiene mi hijo", "qué tiene"]):
            respuesta = _explicar_diagnosticos(informe)
            sugerencias = ["¿Por qué se recomiendan estos ejercicios?", "¿Qué significan los puntajes MFCC?"]
            
        elif any(p in pregunta for p in ["ejercicio", "ejercicios", "recomienda", "practicar"]):
            respuesta = _explicar_ejercicios(informe)
            sugerencias = ["¿Qué diagnósticos tiene mi hijo?", "¿Qué tan seguro es este diagnóstico?"]
            
        elif any(p in pregunta for p in ["mfcc", "puntaje", "audio", "grabación", "sonido"]):
            respuesta = _explicar_puntajes_mfcc(informe)
            sugerencias = ["¿Qué diagnósticos tiene mi hijo?", "¿Por qué se recomiendan estos ejercicios?"]
            
        elif any(p in pregunta for p in ["seguro", "confiable", "certeza", "confiabilidad"]):
            respuesta = _explicar_confiabilidad(informe)
            sugerencias = ["¿Qué diagnósticos tiene mi hijo?", "¿Qué significan los puntajes MFCC?"]
            
        elif any(p in pregunta for p in ["progreso", "avance", "evolución", "mejorado"]):
            respuesta = _explicar_progreso(informe)
            sugerencias = ["¿Qué diagnósticos tiene mi hijo?", "¿Por qué se recomiendan estos ejercicios?"]
            
        else:
            respuesta = _respuesta_general(informe)
            sugerencias = [
                "¿Qué diagnósticos tiene mi hijo?",
                "¿Por qué se recomiendan estos ejercicios?",
                "¿Qué significan los puntajes MFCC?",
                "¿Qué tan seguro es este diagnóstico?"
            ]
        
        return {
            "status": "success",
            "respuesta": respuesta,
            "sugerencias": sugerencias,
            "hechos_activados": []
        }
        
    except Exception as e:
        logger.error(f"Error en módulo explicativo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _explicar_diagnosticos(informe: dict) -> str:
    """Explica los diagnósticos encontrados."""
    diagnosticos = informe.get('diagnosticos', [])
    diagnosticos_filtrados = [d for d in diagnosticos if d.get('fc_total', 0) > 0.5]
    
    if not diagnosticos_filtrados:
        return """✅ **No se encontraron diagnósticos con certeza suficiente**

Esto es una buena noticia. Significa que el desarrollo de tu hijo está dentro de lo esperado para su edad.

**Recomendación:** Continúa con la estimulación en casa y realiza una reevaluación anual de control."""
    
    respuesta = "🔬 **Diagnósticos detectados en esta evaluación:**\n\n"
    for diag in diagnosticos_filtrados:
        certeza = diag.get('fc_total', 0) * 100
        nombre = diag.get('nombre_diag', '')
        respuesta += f"• **{nombre}** (certeza: {certeza:.1f}%)\n"
    
    respuesta += "\n**¿Qué significa esto?**\n"
    respuesta += "Estos diagnósticos se basan en la combinación de:\n"
    respuesta += "1. La pronunciación evaluada por el sistema (MFCC)\n"
    respuesta += "2. Los antecedentes reportados en la anamnesis\n"
    respuesta += "3. El rendimiento histórico del niño en ejercicios previos\n\n"
    respuesta += "El porcentaje de certeza indica qué tan sólida es la evidencia. Cuanto más alto, más confiable es el diagnóstico."
    
    return respuesta


def _explicar_ejercicios(informe: dict) -> str:
    """Explica por qué se recomiendan ciertos ejercicios."""
    plan = informe.get('plan', [])
    
    if not plan:
        return "📝 **No hay ejercicios específicos recomendados**\n\nCompleta más evaluaciones para obtener un plan de intervención personalizado."
    
    respuesta = "🎯 **¿Por qué estos ejercicios?**\n\n"
    respuesta += "Los ejercicios recomendados fueron seleccionados automáticamente por el sistema basado en:\n\n"
    respuesta += "1. **Los diagnósticos detectados** - Cada diagnóstico está asociado a ejercicios específicos\n"
    respuesta += "2. **El nivel de dificultad apropiado para su edad** - Ejercicios ni muy fáciles ni muy difíciles\n"
    respuesta += "3. **El rendimiento histórico** - Se priorizan áreas con menor puntaje\n\n"
    
    respuesta += "**Ejercicios sugeridos:**\n"
    for e in plan[:5]:
        nivel = e.get('nivel_dificultad', 'Medio')
        nombre = e.get('nombre_ejercicio', '')
        nivel_emoji = "🟢" if nivel == "Bajo" else "🟡" if nivel == "Medio" else "🔴"
        respuesta += f"{nivel_emoji} **{nombre}** (Nivel: {nivel})\n"
    
    respuesta += "\n💡 **Recomendación:** Practica estos ejercicios con tu hijo 3-4 veces por semana para mejores resultados."
    
    return respuesta


def _explicar_puntajes_mfcc(informe: dict) -> str:
    """Explica qué significan los puntajes MFCC."""
    mfcc_scores = informe.get('mfcc_scores', [])
    
    if not mfcc_scores:
        return "🎙️ **No hay puntajes MFCC disponibles**\n\nAsegúrate de haber realizado las grabaciones de audio durante la evaluación."
    
    respuesta = "🎙️ **¿Qué significan los puntajes MFCC?**\n\n"
    respuesta += "El MFCC (Mel-Frequency Cepstral Coefficients) es una tecnología que analiza cómo se acerca la pronunciación de tu hijo al patrón esperado.\n\n"
    respuesta += "**Interpretación de los puntajes:**\n"
    respuesta += "• **>70%** → ✅ Pronunciación correcta. El niño domina este sonido.\n"
    respuesta += "• **40-70%** → ⚠️ En desarrollo. Necesita práctica guiada.\n"
    respuesta += "• **<40%** → 🔴 Dificultad significativa. Priorizar en terapia.\n\n"
    
    respuesta += "**Resultados de esta evaluación:**\n"
    for score in mfcc_scores[:5]:
        valor = score.get('score', 0)
        descripcion = score.get('descripcion', 'Fonema')[:30]
        if valor >= 0.7:
            emoji = "✅"
        elif valor >= 0.4:
            emoji = "⚠️"
        else:
            emoji = "🔴"
        respuesta += f"{emoji} **{descripcion}**: {valor*100:.1f}%\n"
    
    return respuesta


def _explicar_confiabilidad(informe: dict) -> str:
    """Explica la confiabilidad de los diagnósticos."""
    diagnosticos = informe.get('diagnosticos', [])
    max_certeza = max([d.get('fc_total', 0) for d in diagnosticos]) if diagnosticos else 0
    
    respuesta = f"🔬 **Confiabilidad del diagnóstico ({max_certeza*100:.0f}% máxima)**\n\n"
    respuesta += "La certeza se calcula combinando varios factores:\n\n"
    respuesta += "1. **Evidencia directa** (puntajes MFCC del audio) - 70% del peso\n"
    respuesta += "2. **Anamnesis** (antecedentes reportados por usted)\n"
    respuesta += "3. **Rendimiento histórico** (prácticas anteriores) - 30% del peso\n"
    respuesta += "4. **Reglas clínicas** (pesos asignados por expertos)\n\n"
    respuesta += "**Interpretación de la certeza:**\n"
    respuesta += "• >70%: Evidencia sólida. El diagnóstico es muy confiable.\n"
    respuesta += "• 50-70%: Evidencia moderada. Considerar seguimiento.\n"
    respuesta += "• <50%: Insuficiente para diagnóstico concluyente.\n\n"
    respuesta += "La confiabilidad aumenta cuando múltiples fuentes de evidencia coinciden."
    
    return respuesta


def _explicar_progreso(informe: dict) -> str:
    """Explica el progreso del niño."""
    progreso = informe.get('progreso', {})
    completados = progreso.get('ejercicios_completados', 0)
    total = progreso.get('ejercicios_recomendados', 1)
    porcentaje = progreso.get('porcentaje', 0)
    
    respuesta = f"📈 **Progreso actual: {porcentaje:.0f}% de la evaluación completada**\n\n"
    respuesta += f"Has completado {completados} de {total} ejercicios recomendados.\n\n"
    
    if porcentaje < 30:
        respuesta += "🔹 **Vas empezando.** Lo importante es la constancia, no la velocidad.\n"
        respuesta += "   Continúa con los ejercicios y verás mejoras progresivas."
    elif porcentaje < 70:
        respuesta += "🔹 **¡Vas por buen camino!** Sigue practicando los ejercicios recomendados.\n"
        respuesta += "   La práctica regular es clave para la mejora."
    else:
        respuesta += "🔹 **¡Excelente progreso!** Estás aprovechando muy bien la terapia.\n"
        respuesta += "   Mantén este ritmo de trabajo."
    
    respuesta += "\n\n**¿Cómo se ajusta la dificultad?**\n"
    respuesta += "El sistema usa la Zona de Desarrollo Próximo (ZDP):\n"
    respuesta += "• Supera 70% de precisión → Sube de nivel\n"
    respuesta += "• Baja de 40% de precisión → Refuerza nivel actual\n"
    respuesta += "• Entre 40-70% → Continúa practicando al mismo nivel"
    
    return respuesta


def _respuesta_general(informe: dict) -> str:
    """Respuesta general para preguntas no clasificadas."""
    return """🔍 **Módulo Explicativo - Sistema Experto Fonoaudiológico**

Puedo ayudarte a entender:

• **Diagnósticos** → ¿Qué diagnósticos tiene mi hijo?
• **Ejercicios** → ¿Por qué se recomiendan estos ejercicios?
• **Puntajes MFCC** → ¿Qué significan los puntajes de audio?
• **Confiabilidad** → ¿Qué tan seguros son estos diagnósticos?
• **Progreso** → ¿Cómo va evolucionando mi hijo?

**Consejo:** Sé específico en tus preguntas para obtener mejores respuestas.

¿Qué te gustaría saber sobre la evaluación de tu hijo?"""