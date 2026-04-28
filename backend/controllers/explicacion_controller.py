from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from models.conexion_db import db_admin
from services.motor_inferencia import MotorInferencia
from utils.logger import get_logger
import re
from datetime import datetime
import unicodedata

logger = get_logger(__name__)

router = APIRouter()
motor = MotorInferencia()

# Almacenar conversaciones
conversaciones = {}


class MensajeChat(BaseModel):
    id_nino: int
    id_evaluacion: int
    mensaje: str


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def normalizar_texto(texto: str) -> str:
    """Normaliza texto: minúsculas, sin acentos."""
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'[¿?¡!.,;:()\[\]{}"\']', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def obtener_descripcion_hecho(id_hecho: int) -> str:
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT descripcion FROM base_hechos WHERE id_hecho = %s", (id_hecho,))
            row = cursor.fetchone()
            return row['descripcion'] if row else "Indicador clínico"
    except:
        return "Indicador clínico"


def traducir_diagnostico(nombre: str) -> str:
    traducciones = {
        "Trastorno de la Percepción Temporal": "le cuesta seguir el ritmo o entender conceptos como antes/después",
        "Trastorno Mixto Receptivo-Expresivo": "le cuesta entender lo que le dicen y también expresar lo que piensa",
        "Trastorno Fonológico": "le cuesta ordenar los sonidos al hablar",
        "Trastorno Pragmático": "le cuesta seguir las reglas de una conversación",
        "Dislalia Funcional": "le cuesta pronunciar un sonido específico",
        "Apraxia del Habla Infantil": "su cerebro tiene dificultades para coordinar la boca al hablar",
        "Disartria Pediátrica": "tiene debilidad en los músculos de la boca",
        "TPAC": "se distrae cuando hay ruido de fondo",
        "Dislexia Fonológica": "le cuesta relacionar letras con sonidos",
        "Tartamudez": "se traba al hablar o repite sílabas"
    }
    
    for key, value in traducciones.items():
        if key.lower() in nombre.lower() or nombre.lower() in key.lower():
            return value
    
    if "percepcion" in nombre.lower() or "temporal" in nombre.lower():
        return "le cuesta seguir el ritmo o entender conceptos como antes/después"
    
    return "tiene dificultades en el área del lenguaje"


# =========================================================
# EXPLICACIONES DETALLADAS DE EJERCICIOS
# =========================================================

def obtener_ejemplos_ejercicio(nombre_ejercicio: str) -> dict:
    ejemplos = {
        "palabra corta": {
            "descripcion_detallada": "Este ejercicio ayuda a mejorar la pronunciación de palabras cortas y claras.",
            "ejemplos": [
                "🎲 **Juego de la lotería:** Haz tarjetas con dibujos de palabras simples (sol, pan, mar, pez, red, flor). Pídele que nombre cada dibujo.",
                "🎤 **Repite conmigo:** Di una palabra y pídele que la repita. Ejemplos: 'sol', 'luz', 'tren', 'flor', 'pez'.",
                "🐶 **Adivina la palabra:** Describe algo y que adivine. 'Es amarillo, brilla en el día → sol'"
            ],
            "actividades_casa": [
                "📚 **Lectura de cuentos cortos:** Señala dibujos y pídele que diga lo que ve.",
                "🎨 **Dibujar y nombrar:** Dibujen juntos objetos y que nombre lo que dibujaron.",
                "🗣️ **Espejo:** Pídele que se mire al espejo mientras pronuncia las palabras."
            ],
            "consejos": "Empieza con palabras de 3 letras. Si le cuesta, no lo presiones, solo muéstrale otra vez."
        },
        "soplo": {
            "descripcion_detallada": "Fortalece los músculos de la respiración y mejora la emisión del aire al hablar.",
            "ejemplos": [
                "🕯️ **Soplar una vela:** Pon una vela encendida a 10 cm y pídele que la apague soplando.",
                "🧴 **Burbujas:** Soplar con un popote para hacer burbujas en un vaso con agua y jabón.",
                "📄 **Carrera de papelitos:** Pon un papelito en la mesa y que lo mueva soplando hasta la meta."
            ],
            "actividades_casa": [
                "🎈 **Inflar globos:** Inflar globos pequeños fortalece el soplo.",
                "📯 **Pitos y silbatos:** Jugar con instrumentos de viento.",
                "🥤 **Soplar con popote:** Mover bolitas de papel soplando por un popote."
            ],
            "consejos": "Hazlo divertido. Compite con él a ver quién sopla más lejos."
        },
        "turnos de habla": {
            "descripcion_detallada": "Enseña al niño a esperar su turno para hablar y a respetar las reglas de conversación.",
            "ejemplos": [
                "🗣️ **Mi turno, tu turno:** Usa un objeto (pelota, juguete) para indicar quién habla.",
                "📱 **Juego del teléfono:** 'Llamada' con teléfonos de juguete, turnándose para hablar."
            ],
            "actividades_casa": [
                "🍽️ **Conversaciones en la mesa:** En la cena, turnarse para contar cómo estuvo el día.",
                "🎲 **Juegos de mesa:** Juegos por turnos (lotería, memorama) enseñan a esperar.",
                "📖 **Lectura por turnos:** Leer un cuento, una frase cada uno."
            ],
            "consejos": "Modela el comportamiento. Respeta su turno y cuando hable, escucha sin interrumpir."
        },
        "praxias": {
            "descripcion_detallada": "Ejercicios de lengua y labios para mejorar la movilidad y coordinación de los órganos del habla.",
            "ejemplos": [
                "👅 **La lengua curiosa:** Sacar la lengua y tocar la nariz, la barbilla, las comisuras de los labios.",
                "😛 **Sonidos de lengua:** Hacer sonidos de caballo (trotar con la lengua).",
                "👄 **Besos al aire:** Enviar besos haciendo 'muá' con los labios."
            ],
            "actividades_casa": [
                "🎭 **Muecas en el espejo:** Hacer muecas frente al espejo (labios hacia arriba, hacia abajo, sonrisa grande).",
                "🍭 **Lamerse los labios:** Comer una paleta o helado y lamerse los labios.",
                "🐮 **Imitar animales:** Hacer sonidos de animales (vaca: muuu, perro: guau, gato: miau)."
            ],
            "consejos": "Hazlo divertido, como un juego de 'haz lo que yo hago'. No lo fuerces si le cuesta."
        }
    }
    
    for key, info in ejemplos.items():
        if key in nombre_ejercicio.lower():
            return info
    return None


def explicar_ejercicio_especifico(nombre_ejercicio: str, plan: list, nombre_nino: str) -> dict:
    for e in plan:
        nombre_e = e.get('nombre_ejercicio', '').lower()
        nombre_ejercicio_limpio = nombre_ejercicio.lower().replace("el ejercicio de ", "").replace("el ", "").strip()
        
        if nombre_ejercicio_limpio in nombre_e or nombre_e in nombre_ejercicio_limpio:
            nombre = e.get('nombre_ejercicio', 'Ejercicio')
            desc = e.get('descripcion_instrucciones', 'Sigue las instrucciones')
            info = obtener_ejemplos_ejercicio(nombre)
            
            respuesta = f"🎯 **{nombre}**\n\n{desc}\n\n"
            
            if info:
                respuesta += f"**📖 ¿Para qué sirve?**\n{info['descripcion_detallada']}\n\n"
                respuesta += f"**🎲 Ejemplos prácticos:**\n"
                for ej in info['ejemplos'][:2]:
                    respuesta += f"   {ej}\n"
                respuesta += f"\n**🏠 Actividades para hacer en casa:**\n"
                for act in info['actividades_casa'][:2]:
                    respuesta += f"   {act}\n"
                respuesta += f"\n**💡 Consejo importante:** {info['consejos']}\n\n"
            else:
                respuesta += "**Paso a paso:**\n"
                respuesta += "1. Busca un lugar tranquilo sin distracciones\n"
                respuesta += "2. Muéstrale cómo se hace primero tú\n"
                respuesta += "3. Pídele que lo intente\n"
                respuesta += "4. Si se equivoca, no lo corrijas bruscamente\n"
                respuesta += "5. Celebra cuando lo intente, aunque no salga perfecto\n\n"
            
            respuesta += "📌 **Recuerda:** La práctica diaria de 10-15 minutos es más efectiva.\n\n"
            respuesta += "¿Necesitas que te explique otro ejercicio o quieres ideas de otros juegos?"
            
            return {
                "respuesta": respuesta,
                "sugerencias": ["Explícame otro ejercicio", "Ideas para otros juegos", "Volver"]
            }
    return None


# =========================================================
# FUNCIONES DE RESPUESTA
# =========================================================

def responder_dificultades(nombre_nino: str, edad: int, diagnosticos: list) -> dict:
    if not diagnosticos:
        return {
            "respuesta": f"✅ **{nombre_nino} está bien**\n\nTiene {edad} años y la evaluación no mostró dificultades significativas.\n\n¿Quieres ideas de actividades para hacer en casa?",
            "sugerencias": ["¿Qué actividades puedo hacer en casa?", "¿Cómo va su progreso?"]
        }
    
    respuesta = f"📋 **Lo que encontramos en {nombre_nino}**\n\nTiene {edad} años:\n\n"
    for d in diagnosticos[:2]:
        nombre = d.get('nombre_diag', '')
        certeza = d.get('fc_total', 0) * 100
        traduccion = traducir_diagnostico(nombre)
        respuesta += f"• **{traduccion}**\n"
        if certeza >= 70:
            respuesta += f"  → Estamos bastante seguros de esto ({certeza:.0f}%).\n\n"
        elif certeza >= 50:
            respuesta += f"  → Hay evidencia suficiente para considerarlo ({certeza:.0f}%).\n\n"
        else:
            respuesta += f"  → La evidencia es leve ({certeza:.0f}%).\n\n"
    
    respuesta += "¿Te gustaría saber por qué llegamos a esta conclusión o qué ejercicios pueden ayudar?"
    
    return {
        "respuesta": respuesta,
        "sugerencias": ["¿Por qué llegaron a esa conclusión?", "¿Qué ejercicios me recomiendas?"]
    }


def responder_razonamiento(nombre_nino: str, diagnosticos: list, informe: dict) -> dict:
    mfcc_scores = informe.get('mfcc_scores', [])
    anamnesis = informe.get('anamnesis', [])
    
    if not diagnosticos:
        return {
            "respuesta": f"🔍 No hay un diagnóstico específico. Todo está dentro de lo esperado para su edad.\n\n¿Quieres ideas de actividades para hacer en casa?",
            "sugerencias": ["¿Qué actividades puedo hacer en casa?"]
        }
    
    respuesta = f"🔍 **¿Cómo llegamos a esta conclusión sobre {nombre_nino}?**\n\n"
    respuesta += "Te explico de forma sencilla:\n\n"
    
    if mfcc_scores:
        bajos = [s for s in mfcc_scores if s.get('score', 0) < 0.4]
        if bajos:
            respuesta += "**1. Análisis de la voz**\n"
            for s in bajos[:3]:
                desc = s.get('descripcion', 'Fonema')
                puntaje = s.get('score', 0) * 100
                respuesta += f"   • {desc}: solo alcanza un {puntaje:.0f}% de precisión\n"
            respuesta += "\n"
    
    if anamnesis:
        respuesta += "**2. Lo que me contaste**\n"
        for a in anamnesis[:3]:
            respuesta += f"   • {a.get('descripcion', '')[:70]}\n"
        respuesta += "\n"
    
    respuesta += "**3. Patrones que detectamos**\n"
    hechos_vistos = set()
    for d in diagnosticos:
        for h in d.get('hechos_disparadores', [])[:3]:
            if h not in hechos_vistos:
                hechos_vistos.add(h)
                desc = obtener_descripcion_hecho(h)
                if desc:
                    respuesta += f"   • {desc[:80]}\n"
    
    respuesta += "\n💡 **En resumen:** Juntando cómo habla, lo que me contaste y estos patrones, el sistema determina qué necesita practicar más.\n\n"
    respuesta += "¿Te gustaría saber qué ejercicios pueden ayudarle?"
    
    return {
        "respuesta": respuesta,
        "sugerencias": ["¿Qué ejercicios me recomiendas?", "¿Cómo sé si está mejorando?"]
    }


def responder_ejercicios(nombre_nino: str, plan: list, edad: int) -> dict:
    if not plan:
        return {
            "respuesta": f"📝 Por ahora no hay ejercicios específicos. Te recomiendo leer cuentos con {nombre_nino} todos los días y conversar con él mirándolo a los ojos.\n\n¿Quieres más ideas generales?",
            "sugerencias": ["Dame más ideas", "¿Cuándo reevaluarlo?"]
        }
    
    faciles = [e for e in plan if e.get('nivel_dificultad') == 'Bajo'][:3]
    
    respuesta = f"🎯 **Ejercicios recomendados para {nombre_nino}**\n\n"
    respuesta += "Te recomiendo empezar con estos ejercicios:\n"
    for e in faciles:
        nombre = e.get('nombre_ejercicio', 'Ejercicio')
        respuesta += f"• **{nombre}**\n"
    respuesta += "\n💡 **Consejos importantes:**\n"
    respuesta += "• 10-15 minutos al día (mejor poco pero constante)\n"
    respuesta += "• Lugar tranquilo, sin tele ni ruido\n"
    respuesta += "• Tú primero - muéstrale cómo se hace\n"
    respuesta += "• Celebra los intentos, aunque no salga perfecto\n\n"
    respuesta += "¿Quieres que te explique cómo hacer alguno de estos ejercicios paso a paso?"
    
    return {
        "respuesta": respuesta,
        "sugerencias": ["Sí, explícame uno", "¿Cómo sé si está mejorando?"]
    }


def responder_progreso(nombre_nino: str, informe: dict) -> dict:
    progreso = informe.get('progreso', {})
    completados = progreso.get('ejercicios_completados', 0)
    total = progreso.get('ejercicios_recomendados', 1)
    porcentaje = progreso.get('porcentaje', 0)
    
    if completados == 0:
        return {
            "respuesta": f"📈 **Progreso de {nombre_nino}**\n\nTodavía es pronto para ver cambios. Te recomiendo practicar los ejercicios durante 2-3 semanas y luego volver a consultar.\n\n¿Necesitas que te recuerde los ejercicios?",
            "sugerencias": ["¿Qué ejercicios debo hacer?"]
        }
    
    respuesta = f"📈 **¿Cómo saber si {nombre_nino} está mejorando?**\n\n"
    respuesta += f"Hasta ahora ha completado **{completados} de {total} ejercicios** ({porcentaje:.0f}% del plan).\n\n"
    
    if porcentaje >= 70:
        respuesta += "🎉 **¡Excelente!** Sigue así.\n\n"
    elif porcentaje >= 40:
        respuesta += "📊 **¡Buen avance!** La práctica constante está dando resultados.\n\n"
    else:
        respuesta += "📌 **Recién empezando.** Lo importante es la constancia.\n\n"
    
    respuesta += "**🔍 Señales de mejora que puedes observar:**\n"
    respuesta += "• Pronuncia mejor los sonidos que antes le costaban\n"
    respuesta += "• Habla con más confianza\n"
    respuesta += "• Usa palabras más largas o frases más complejas\n\n"
    
    respuesta += "💡 La clave es la práctica diaria, aunque sea por pocos minutos.\n\n"
    respuesta += "¿Necesitas más consejos o quieres que te explique algún ejercicio?"
    
    return {
        "respuesta": respuesta,
        "sugerencias": ["Explícame un ejercicio", "¿Cómo motivarlo?", "¿Cuándo reevaluarlo?"]
    }


def responder_motivacion(nombre_nino: str) -> dict:
    return {
        "respuesta": f"😊 **Cómo motivar a {nombre_nino}**\n\n"
        "1. **Hazlo divertido** - Usa juegos, canciones o marionetas\n"
        "2. **Sesiones cortas** - Mejor 5 minutos felices que 20 de frustración\n"
        "3. **Celebra los intentos** - '¡Muy bien! ¡Lo intentaste!' aunque no salga perfecto\n"
        "4. **Sé paciente** - No lo presiones si está cansado o de mal humor\n"
        "5. **Tú primero** - Muéstrale cómo se hace y luego pídele que intente\n"
        "6. **Usa premios pequeños** - Stickers, dibujos, un cuento especial al terminar\n\n"
        "💡 **Recuerda:** El aprendizaje lleva tiempo. Lo importante es que asocie la práctica con momentos agradables.\n\n"
        "¿Te gustaría más ideas para hacer los ejercicios más divertidos?",
        "sugerencias": ["Más ideas divertidas", "¿Qué ejercicios son más fáciles?"]
    }


def responder_reevaluacion(nombre_nino: str) -> dict:
    return {
        "respuesta": f"📅 **¿Cuándo reevaluarlo?**\n\nSe recomienda reevaluar a {nombre_nino} después de **3 meses** de práctica constante.\n\n"
        "Esto permite ver los avances reales y ajustar los ejercicios si es necesario.\n\n"
        "💡 La práctica diaria de 10-15 minutos es clave para ver mejoras.\n\n"
        "¿Te gustaría que te ayude a planificar una rutina semanal?",
        "sugerencias": ["Ayúdame con una rutina", "¿Qué ejercicios empezar?"]
    }


def responder_escuela(nombre_nino: str, edad: int) -> dict:
    return {
        "respuesta": f"📚 **¿Afecta en la escuela?**\n\nDependiendo de las dificultades, podría afectar en lectura, seguir instrucciones o participación en clases.\n\n"
        "💡 **Recomendaciones prácticas:**\n"
        "1. Habla con sus profesores sobre las dificultades específicas\n"
        "2. Pide que lo sienten en un lugar adelante, lejos de ruidos\n"
        "3. Refuerza en casa lo que ve en el colegio con juegos\n\n"
        f"A los {edad} años, con apoyo en casa y en el colegio, suele mejorar bastante.\n\n"
        "¿Quieres más consejos?",
        "sugerencias": ["Más consejos", "¿Qué ejercicios ayudan para la escuela?"]
    }


def responder_confiabilidad(diagnosticos: list) -> dict:
    if not diagnosticos:
        return {
            "respuesta": "🔬 **Confiabilidad del diagnóstico**\n\nNo hay diagnósticos con certeza suficiente, lo que es buena señal. Significa que no hay evidencia clara de dificultades.\n\n¿Quieres ideas de actividades para hacer en casa?",
            "sugerencias": ["¿Qué actividades puedo hacer en casa?"]
        }
    
    max_certeza = max([d.get('fc_total', 0) for d in diagnosticos]) * 100
    
    if max_certeza >= 70:
        nivel = "ALTA"
        explicacion = "Puedes confiar en estos resultados. Las diferentes fuentes coinciden entre sí."
    elif max_certeza >= 50:
        nivel = "MODERADA"
        explicacion = "Hay buena evidencia, pero un seguimiento en unos meses ayudaría a confirmar."
    else:
        nivel = "LEVE"
        explicacion = "La información es limitada. Se necesitan más datos para estar seguros."
    
    return {
        "respuesta": f"🔬 **¿Qué tan seguro es este diagnóstico?**\n\n"
        f"La confiabilidad es **{nivel}** ({max_certeza:.0f}%)\n\n"
        f"{explicacion}\n\n"
        "**¿Cómo se calcula?**\n"
        "• Análisis de la voz (70% del peso)\n"
        "• Anamnesis (lo que me contaste, 20%)\n"
        "• Rendimiento histórico (prácticas anteriores, 10%)\n\n"
        "¿Te gustaría saber más?",
        "sugerencias": ["¿Qué ejercicios me recomiendas?", "¿Cómo sé si está mejorando?"]
    }


def responder_ideas_casa_generales() -> dict:
    return {
        "respuesta": "🏠 **Actividades para hacer en casa**\n\n"
        "**📖 Lectura (10-15 min diarios):**\n"
        "• Lee cuentos con ilustraciones grandes\n"
        "• Señala los dibujos y pregúntale qué ve\n"
        "• Pídele que invente un final diferente\n\n"
        
        "**🎲 Juegos de palabras:**\n"
        "• **Rimar palabras:** 'casa' con 'pasa', 'sol' con 'col'\n"
        "• **Decir palabras que empiecen igual:** 'manzana, mano, mamá'\n"
        "• **Teléfono descompuesto:** Susurrar una palabra y que la repita\n\n"
        
        "**🗣️ Juegos de conversación:**\n"
        "• **Cómo estuvo tu día:** Contar qué hizo en el colegio\n"
        "• **Adivina el objeto:** Describir algo y que adivine qué es\n\n"
        
        "**🎨 Juegos con sonidos:**\n"
        "• **Imitar animales:** '¿cómo hace el perro?', 'el gato'\n"
        "• **Canciones infantiles:** Cantar y hacer gestos\n\n"
        
        "💡 **La fórmula del éxito:** 10 minutos diarios + paciencia = mejora continua.\n\n"
        "¿Te gustaría que te recomiende ejercicios específicos?",
        "sugerencias": ["Sí, según sus dificultades", "Ejercicios para la pronunciación"]
    }


def responder_como_hacer_ejercicios_detallado(plan: list, nombre_nino: str) -> dict:
    if not plan:
        return {
            "respuesta": f"📝 **Actividades generales para hacer en casa con {nombre_nino}**\n\n"
            "**Lectura diaria (10 minutos):** Leer cuentos juntos, señalar dibujos y preguntarle qué ve.\n\n"
            "**Juegos de palabras:** Rimar palabras (casa-pasa, sol-col), decir palabras que empiecen con la misma letra.\n\n"
            "**Conversación:** Háblale mirándolo a los ojos, dale tiempo para responder.\n\n"
            "💡 **Lo más importante:** 10-15 minutos diarios son más efectivos.\n\n"
            "¿Te gustaría ideas más específicas?",
            "sugerencias": ["Ideas para la 'R'", "Ideas para la atención"]
        }
    
    faciles = [e for e in plan if e.get('nivel_dificultad') == 'Bajo'][:2]
    
    respuesta = f"🎯 **Cómo practicar los ejercicios en casa con {nombre_nino}**\n\n"
    respuesta += "**✅ Consejos para TODOS los ejercicios:**\n"
    respuesta += "• **10-15 minutos al día** (mejor poco pero constante)\n"
    respuesta += "• **Lugar tranquilo** sin tele ni ruido\n"
    respuesta += "• **Tú primero** - muéstrale cómo se hace\n"
    respuesta += "• **Celebra los intentos** - aunque no salga perfecto\n"
    respuesta += "• **Si está cansado o de mal humor, mejor otro día**\n\n"
    
    respuesta += "**📋 Ejercicios específicos con ejemplos:**\n\n"
    
    for e in faciles:
        nombre = e.get('nombre_ejercicio', 'Ejercicio')
        info = obtener_ejemplos_ejercicio(nombre)
        
        if info:
            respuesta += f"**• {nombre}**\n"
            respuesta += f"   {info['descripcion_detallada']}\n"
            respuesta += f"   🎲 **Ejemplo:** {info['ejemplos'][0]}\n"
            respuesta += f"   🏠 **En casa:** {info['actividades_casa'][0]}\n\n"
    
    respuesta += "✨ **¿Quieres que te explique alguno de estos ejercicios con más detalle?**"
    
    return {
        "respuesta": respuesta,
        "sugerencias": ["Explícame el primer ejercicio", "Dame ideas para otros juegos", "¿Cómo motivarlo?"]
    }


# =========================================================
# PROCESAMIENTO PRINCIPAL
# =========================================================

def procesar_todo(mensaje: str, nombre_nino: str, edad: int, informe: dict, id_nino: int, contexto: dict, tono: str) -> dict:
    msg = normalizar_texto(mensaje)
    
    diagnosticos = informe.get('diagnosticos', [])
    diagnosticos_relevantes = [d for d in diagnosticos if d.get('fc_total', 0) > 0.5]
    plan = informe.get('plan', [])
    
    ultimo_tema = contexto.get("ultimo_tema", "")
    
    # =========================================================
    # RESPUESTAS AFIRMATIVAS
    # =========================================================
    if msg in ["si", "sí", "ok", "vale", "dale", "simon"] or "por favor" in msg:
        if ultimo_tema == "ofreciendo_explicacion":
            if plan:
                primer_ej = plan[0]
                nombre_ej = primer_ej.get('nombre_ejercicio', '')
                resultado = explicar_ejercicio_especifico(nombre_ej, plan, nombre_nino)
                if resultado:
                    contexto["ultimo_tema"] = "explicando_ejercicio"
                    return resultado
            return {"respuesta": "No hay ejercicios para explicar aún.", "sugerencias": ["Volver"]}
        
        return {
            "respuesta": f"¡Excelente! ¿Sobre qué quieres saber más? Puedo ayudarte con las dificultades, los ejercicios o el progreso de {nombre_nino}.",
            "sugerencias": [f"¿Qué dificultades tiene {nombre_nino}?", "¿Qué ejercicios me recomiendas?", "¿Cómo va su progreso?"]
        }
    
    # =========================================================
    # VOLVER
    # =========================================================
    if msg in ["volver", "regresar", "atras", "menu", "menu principal"]:
        contexto["ultimo_tema"] = None
        return {
            "respuesta": f"¡Claro! ¿Sobre qué quieres hablar de {nombre_nino}? Puedo contarte sobre sus dificultades, los ejercicios recomendados o su progreso.",
            "sugerencias": [f"¿Qué dificultades tiene {nombre_nino}?", "¿Qué ejercicios me recomiendas?", "¿Cómo va su progreso?"]
        }
    
    # =========================================================
    # MOTIVACIÓN
    # =========================================================
    if re.search(r"(motivar|animo|animar|alentar|entusiasmar|como lo animo|como lo ayudo|como ayudarlo|como motivarlo|como lo motivo)", msg):
        return responder_motivacion(nombre_nino)
    
    # =========================================================
    # REEVALUACIÓN
    # =========================================================
    if re.search(r"(reevalu|proxima evalu|siguiente evalu|cuando debe ser|cuando toca|otra vez evalu|cual es su siguiente evaluacion|cuando hacer|cuando reevaluar)", msg):
        return responder_reevaluacion(nombre_nino)
    
    # =========================================================
    # CÓMO HACER EJERCICIOS
    # =========================================================
    if re.search(r"(como hago los ejercicios|como practicar|explicame como hacer|todos me das las mismas|mismas recomendaciones|como lo hago|como se hacen)", msg):
        return responder_como_hacer_ejercicios_detallado(plan, nombre_nino)
    
    # =========================================================
    # IDEAS GENERALES PARA CASA
    # =========================================================
    if re.search(r"(actividades en casa|que hacer en casa|juegos en casa|ideas para casa|actividades para hacer|que puedo hacer en casa)", msg):
        return responder_ideas_casa_generales()
    
    # =========================================================
    # EXPLICAR EJERCICIO ESPECÍFICO
    # =========================================================
    es_peticion_explicacion = re.search(r"(explic|enseñ|muestram|como se hace|como es el|como lo hacemos|como hago el|como realizo|dime como)", msg)
    ejercicios_conocidos = ["palabra corta", "soplo controlado", "soplo", "turnos de habla", "turno de habla", "praxias", "ritmo", "atencion"]
    
    for nombre_ej in ejercicios_conocidos:
        if nombre_ej in msg:
            if es_peticion_explicacion or "como es" in msg or "como lo hacemos" in msg:
                resultado = explicar_ejercicio_especifico(nombre_ej, plan, nombre_nino)
                if resultado:
                    contexto["ultimo_tema"] = "explicando_ejercicio"
                    contexto["ultimo_ejercicio"] = nombre_ej
                    return resultado
    
    if es_peticion_explicacion and not any(ej in msg for ej in ejercicios_conocidos):
        contexto["ultimo_tema"] = "ofreciendo_explicacion"
        if plan:
            lista_ej = ", ".join([e.get('nombre_ejercicio', '') for e in plan[:3]])
            return {
                "respuesta": f"Claro, puedo explicarte cualquiera de estos ejercicios:\n\n• {lista_ej}\n\n¿Cuál te gustaría que te explique?",
                "sugerencias": [e.get('nombre_ejercicio', '') for e in plan[:3]]
            }
    
    # =========================================================
    # SALUDOS
    # =========================================================
    if msg in ["hola", "buenas", "que tal", "hey", "saludos"]:
        return {
            "respuesta": f"¡Hola! {nombre_nino} tiene {edad} años. ¿Qué te gustaría saber? Puedo contarte sobre sus dificultades, los ejercicios recomendados o su progreso.",
            "sugerencias": [f"¿Qué dificultades tiene {nombre_nino}?", "¿Qué ejercicios me recomiendas?", "¿Cómo va su progreso?"]
        }
    
    # =========================================================
    # DIFICULTADES / DIAGNÓSTICO
    # =========================================================
    if re.search(r"(dificultad|problema|diagnostico|que tiene|que le pasa|que encontraron|como le fue|cual fue|cual es el diagnostico|que diagnostico tiene|que problemas tiene)", msg):
        return responder_dificultades(nombre_nino, edad, diagnosticos_relevantes)
    
    # =========================================================
    # RAZONAMIENTO
    # =========================================================
    if re.search(r"(por que creen|por que crees|como saben|como llegaron|por que piensan|como se determino|como se llego|a que conclusion|por que eso|porque crees eso)", msg):
        return responder_razonamiento(nombre_nino, diagnosticos_relevantes, informe)
    
    # =========================================================
    # EJERCICIOS
    # =========================================================
    if re.search(r"(ejercicio|practicar|actividad|que hacer|que me recomiendas|cuales ejercicios|debe hacer|que ejercicios|que ejercicios le ayuda|que ejercicios debe de hacer)", msg):
        contexto["ultimo_tema"] = "ofreciendo_explicacion"
        return responder_ejercicios(nombre_nino, plan, edad)
    
    # =========================================================
    # PROGRESO
    # =========================================================
    if re.search(r"(progreso|avance|como va|mejorado|cual es su progreso|ha mejorado|como esta|como esta en su progreso)", msg):
        return responder_progreso(nombre_nino, informe)
    
    # =========================================================
    # ESCUELA
    # =========================================================
    if re.search(r"(escuela|colegio|afecta|clases|profesor|rendimiento escolar)", msg):
        return responder_escuela(nombre_nino, edad)
    
    # =========================================================
    # CONFIABILIDAD
    # =========================================================
    if re.search(r"(que tan seguro|confiable|certeza|confianza|que tan confiable)", msg):
        return responder_confiabilidad(diagnosticos_relevantes)
    
    # =========================================================
    # POR DEFECTO
    # =========================================================
    return {
        "respuesta": f"🤔 No entendí bien tu pregunta. ¿Podrías reformularla?\n\nPuedo ayudarte con:\n• Las dificultades de {nombre_nino}\n• Por qué llegamos a esa conclusión\n• Ejercicios para hacer en casa\n• Su progreso\n• Cuándo reevaluarlo\n• Cómo motivarlo\n\n¿Qué te gustaría saber?",
        "sugerencias": [f"¿Qué dificultades tiene {nombre_nino}?", "¿Qué ejercicios me recomiendas?", "¿Cómo va su progreso?", "¿Cómo motivarlo?"]
    }


# =========================================================
# ENDPOINT PRINCIPAL
# =========================================================

@router.post("/chat")
async def chat_explicativo(datos: MensajeChat):
    try:
        from controllers.evaluacion_controller import obtener_informe_clinico, obtener_edad_nino
        
        informe = obtener_informe_clinico(datos.id_nino, datos.id_evaluacion)
        edad = obtener_edad_nino(datos.id_nino)
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT nombre FROM nino WHERE id_nino = %s", (datos.id_nino,))
            nino = cursor.fetchone()
            nombre_nino = nino['nombre'] if nino else "tu hijo"
        
        clave = f"{datos.id_nino}_{datos.id_evaluacion}"
        
        if clave not in conversaciones:
            conversaciones[clave] = {
                "historial": [],
                "ultimo_tema": None,
                "ultimo_ejercicio": None
            }
        
        conversaciones[clave]["historial"].append({"rol": "usuario", "texto": datos.mensaje})
        
        tono = "calido"
        
        respuesta_data = procesar_todo(
            mensaje=datos.mensaje,
            nombre_nino=nombre_nino,
            edad=edad,
            informe=informe,
            id_nino=datos.id_nino,
            contexto=conversaciones[clave],
            tono=tono
        )
        
        conversaciones[clave]["historial"].append({"rol": "asistente", "texto": respuesta_data["respuesta"]})
        
        return {
            "status": "success",
            "respuesta": respuesta_data["respuesta"],
            "sugerencias": respuesta_data.get("sugerencias", []),
            "botones_accion": respuesta_data.get("botones_accion", []),
            "recurso_multimedia": respuesta_data.get("recurso_multimedia"),
            "nivel_usuario": conversaciones[clave]["nivel_usuario"] if "nivel_usuario" in conversaciones[clave] else "principiante"
        }
        
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))