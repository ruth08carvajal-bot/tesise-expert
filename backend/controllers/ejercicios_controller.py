from fastapi import APIRouter, HTTPException
from schemas import GuardarProgresoSchema
from models.conexion_db import db_admin
from controllers.ninos_controller import calcular_edad
from utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter()


@router.get("/mis-ejercicios/{id_nino}")
async def obtener_ejercicios_nino(id_nino: int):
    """
    Obtiene los ejercicios recomendados para un niño específico.
    Similar al plan-evaluacion pero adaptado para el niño.
    """
    try:
        from controllers.evaluacion_controller import construir_plan_personalizado
        
        plan = construir_plan_personalizado(id_nino)
        
        # Formatear para el niño
        ejercicios = []
        for ej in plan.get('plan_adaptativo', []):
            ejercicios.append({
                "id_ejercicio": ej.get('id_ejercicio'),
                "nombre": ej.get('nombre_ejercicio'),
                "descripcion": ej.get('descripcion_instrucciones'),
                "nivel": ej.get('nivel_dificultad'),
                "tipo_apoyo": ej.get('tipo_apoyo'),
                "id_hecho_objetivo": ej.get('id_hecho_objetivo'),
                "rendimiento_previo": ej.get('rendimiento', 0)
            })
        
        # Obtener edad del niño
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT f_nac, nombre FROM nino WHERE id_nino = %s", (id_nino,))
            nino = cursor.fetchone()
            edad = calcular_edad(nino['f_nac']) if nino else 0
        
        return {
            "status": "success",
            "id_nino": id_nino,
            "nombre_nino": nino['nombre'] if nino else "",
            "edad_nino": edad,
            "ejercicios": ejercicios
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo ejercicios para niño {id_nino}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guardar-progreso")
async def guardar_progreso(datos: GuardarProgresoSchema):
    """
    Guarda el progreso de un niño en un ejercicio.
    Actualiza rendimiento_hecho y progreso_nino.
    """
    try:
        # Validar puntaje
        if not 0 <= datos.puntaje_obtenido <= 1:
            raise HTTPException(status_code=400, detail="Puntaje debe estar entre 0 y 1")
        
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # 1. Guardar en progreso_nino (historial de intentos)
            query_progreso = """
                INSERT INTO progreso_nino 
                (id_nino, id_ejercicio, puntaje_obtenido, tiempo_empleado, intento_numero, estado_actual)
                VALUES (%s, %s, %s, %s, 
                    (SELECT COALESCE(MAX(intento_numero), 0) + 1 FROM progreso_nino WHERE id_nino = %s AND id_ejercicio = %s),
                    'completado'
                )
            """
            cursor.execute(query_progreso, (
                datos.id_nino, datos.id_ejercicio, datos.puntaje_obtenido, 
                datos.tiempo_empleado, datos.id_nino, datos.id_ejercicio
            ))
            
            # 2. Obtener el id_hecho asociado a este ejercicio
            cursor.execute("""
                SELECT id_hecho_objetivo FROM catalogo_ejercicios WHERE id_ejercicio = %s
            """, (datos.id_ejercicio,))
            resultado = cursor.fetchone()
            
            if resultado and resultado[0]:
                id_hecho = resultado[0]
                
                # 3. Actualizar rendimiento_hecho (promedio histórico)
                from controllers.evaluacion_controller import actualizar_rendimiento
                actualizar_rendimiento(datos.id_nino, id_hecho, datos.puntaje_obtenido)
            
            conn.commit()
            
            # 4. Calcular nuevo nivel basado en rendimiento (ZPD)
            nuevo_nivel = _calcular_nivel_adaptativo(datos.id_nino, datos.id_ejercicio)
            
            return {
                "status": "success",
                "mensaje": "Progreso guardado correctamente",
                "puntaje": datos.puntaje_obtenido,
                "nivel_sugerido": nuevo_nivel
            }
            
    except Exception as e:
        logger.error(f"Error guardando progreso: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sesion-practica/{id_nino}")
async def obtener_sesion_practica(id_nino: int):
    """Obtiene o crea una sesión de práctica (no reevaluación)"""
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Buscar sesión de práctica existente (tipo 'Practica')
            cursor.execute("""
                SELECT id_ev FROM evaluacion_sesion 
                WHERE id_nino = %s AND tipo_evaluacion = 'Practica'
                LIMIT 1
            """, (id_nino,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                id_evaluacion = resultado[0]
            else:
                # Crear nueva sesión de práctica
                cursor.execute("""
                    INSERT INTO evaluacion_sesion (id_nino, tipo_evaluacion, notas_tutor)
                    VALUES (%s, 'Practica', 'Sesión de práctica libre del niño')
                """, (id_nino,))
                id_evaluacion = cursor.lastrowid
                conn.commit()
            
            return {
                "status": "success",
                "id_evaluacion": id_evaluacion
            }
            
    except Exception as e:
        logger.error(f"Error creando sesión de práctica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progreso-juegos/{id_nino}")
async def obtener_progreso_juegos(id_nino: int):
    """Obtiene el avance por cada juego / ejercicio del niño para mostrar en el progreso."""
    try:
        from controllers.evaluacion_controller import construir_plan_personalizado

        plan = construir_plan_personalizado(id_nino)
        ejercicios_plan = plan.get('plan_adaptativo', [])
        ejercicios_index = {
            ej.get('id_ejercicio'): ej
            for ej in ejercicios_plan
            if ej.get('id_ejercicio')
        }

        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.id_ejercicio, p.puntaje_obtenido, p.tiempo_empleado,
                       p.intento_numero, p.fecha_realizacion,
                       c.nombre_ejercicio, c.nivel_dificultad, c.descripcion_instrucciones,
                       c.tipo_apoyo
                FROM progreso_nino p
                LEFT JOIN catalogo_ejercicios c ON p.id_ejercicio = c.id_ejercicio
                WHERE p.id_nino = %s
                ORDER BY p.fecha_realizacion ASC
            """, (id_nino,))
            progreso_rows = cursor.fetchall()

        juegos_map = {}
        for row in progreso_rows:
            juego = juegos_map.setdefault(row['id_ejercicio'], {
                'id_ejercicio': row['id_ejercicio'],
                'nombre': row.get('nombre_ejercicio') or ejercicios_index.get(row['id_ejercicio'], {}).get('nombre_ejercicio', 'Juego'),
                'descripcion': row.get('descripcion_instrucciones') or ejercicios_index.get(row['id_ejercicio'], {}).get('descripcion_instrucciones', ''),
                'nivel': row.get('nivel_dificultad') or ejercicios_index.get(row['id_ejercicio'], {}).get('nivel_dificultad', 'Bajo'),
                'tipo_apoyo': row.get('tipo_apoyo') or ejercicios_index.get(row['id_ejercicio'], {}).get('tipo_apoyo', ''),
                'intentos': 0,
                'puntajes': [],
                'tiempo_total': 0,
                'ultimo_intento': None,
                'ultima_fecha': None
            })
            juego['intentos'] += 1
            juego['puntajes'].append(row['puntaje_obtenido'] or 0)
            juego['tiempo_total'] += row['tiempo_empleado'] or 0
            if row['fecha_realizacion']:
                juego['ultima_fecha'] = row['fecha_realizacion'].strftime('%d/%m/%Y')
            juego['ultimo_intento'] = row['intento_numero']

        juegos = []
        for ej in ejercicios_plan:
            id_ejercicio = ej.get('id_ejercicio')
            registro = juegos_map.get(id_ejercicio, None)
            promedio = 0
            progreso = 0
            intentos = 0
            ultimo_fecha = None
            tiempo_total = 0
            estado = 'Pendiente'
            if registro:
                intentos = registro['intentos']
                promedio = sum(registro['puntajes']) / len(registro['puntajes']) if registro['puntajes'] else 0
                progreso = round(promedio * 100)
                ultimo_fecha = registro['ultima_fecha']
                tiempo_total = registro['tiempo_total']
                estado = 'Listo' if promedio >= 0.7 else 'En progreso'

            juegos.append({
                'id_ejercicio': id_ejercicio,
                'nombre': ej.get('nombre_ejercicio'),
                'descripcion': ej.get('descripcion_instrucciones'),
                'nivel': ej.get('nivel_dificultad'),
                'tipo_apoyo': ej.get('tipo_apoyo'),
                'intentos': intentos,
                'promedio': round(promedio * 100),
                'ultimo_fecha': ultimo_fecha,
                'tiempo_total': tiempo_total,
                'estado': estado
            })

        total_juegos = len(juegos)
        juegos_con_progreso = len([j for j in juegos if j['intentos'] > 0])
        promedio_general = round((sum(j['promedio'] for j in juegos) / total_juegos) if total_juegos else 0)

        return {
            'status': 'success',
            'id_nino': id_nino,
            'total_juegos': total_juegos,
            'juegos_con_progreso': juegos_con_progreso,
            'juegos': juegos,
            'resumen': {
                'promedio_general': promedio_general,
                'pendientes': total_juegos - juegos_con_progreso,
                'ultimo_actualizado': max((j['ultimo_fecha'] for j in juegos if j['ultimo_fecha']), default=None)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo progreso de juegos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ejercicios-por-nivel/{id_nino}")
async def obtener_ejercicios_por_nivel(id_nino: int):
    """
    Devuelve ejercicios filtrados por ZPD (Zona de Desarrollo Próximo).
    Solo muestra ejercicios del nivel actual y uno siguiente (para desafío).
    """
    try:
        from controllers.evaluacion_controller import (
            construir_plan_personalizado, 
            obtener_rendimiento_hecho
        )
        
        # Obtener plan completo
        plan_completo = construir_plan_personalizado(id_nino)
        todos_ejercicios = plan_completo.get('plan_adaptativo', [])
        
        # Mapeo de niveles
        orden_niveles = ['Bajo', 'Medio', 'Alto']
        
        # Calcular nivel actual basado en rendimiento de ejercicios completados
        nivel_actual = 'Bajo'
        nivel_actual_idx = 0
        
        # Analizar rendimiento de ejercicios ya completados
        ejercicios_con_rendimiento = []
        for ej in todos_ejercicios:
            id_hecho = ej.get('id_hecho_objetivo')
            if id_hecho:
                try:
                    rendimiento = obtener_rendimiento_hecho(id_nino, id_hecho)
                    if rendimiento > 0:
                        ejercicios_con_rendimiento.append({
                            'ejercicio': ej,
                            'rendimiento': rendimiento,
                            'nivel': ej.get('nivel_dificultad', 'Bajo')
                        })
                except:
                    pass
        
        # Calcular estadísticas por nivel
        if ejercicios_con_rendimiento:
            nivel_counts = {'Bajo': 0, 'Medio': 0, 'Alto': 0}
            nivel_sums = {'Bajo': 0, 'Medio': 0, 'Alto': 0}
            
            for item in ejercicios_con_rendimiento:
                nivel = item['nivel']
                if nivel in nivel_counts:
                    nivel_counts[nivel] += 1
                    nivel_sums[nivel] += item['rendimiento']
            
            # Si tiene ejercicios de nivel Medio con buen rendimiento (>70%), sube a Medio
            if nivel_counts['Medio'] > 0 and (nivel_sums['Medio'] / nivel_counts['Medio']) >= 0.7:
                nivel_actual = 'Medio'
                nivel_actual_idx = 1
            
            # Si tiene ejercicios de nivel Alto con buen rendimiento (>70%), sube a Alto
            if nivel_counts['Alto'] > 0 and (nivel_sums['Alto'] / nivel_counts['Alto']) >= 0.7:
                nivel_actual = 'Alto'
                nivel_actual_idx = 2
        
        # Niveles permitidos: actual + uno más (desafío)
        niveles_permitidos = [nivel_actual]
        if nivel_actual_idx + 1 < len(orden_niveles):
            niveles_permitidos.append(orden_niveles[nivel_actual_idx + 1])
        
        # Filtrar y marcar ejercicios
        ejercicios_filtrados = []
        for ej in todos_ejercicios:
            nivel_ej = ej.get('nivel_dificultad', 'Bajo')
            bloqueado = nivel_ej not in niveles_permitidos
            
            id_hecho = ej.get('id_hecho_objetivo')
            rendimiento = 0
            if id_hecho and not bloqueado:
                try:
                    rendimiento = obtener_rendimiento_hecho(id_nino, id_hecho)
                except:
                    pass
            
            ejercicios_filtrados.append({
                "id_ejercicio": ej.get('id_ejercicio'),
                "nombre_ejercicio": ej.get('nombre_ejercicio'),
                "descripcion_instrucciones": ej.get('descripcion_instrucciones'),
                "nivel_dificultad": nivel_ej,
                "tipo_apoyo": ej.get('tipo_apoyo'),
                "id_hecho_objetivo": ej.get('id_hecho_objetivo'),
                "rendimiento_actual": rendimiento,
                "bloqueado": bloqueado
            })
        
        # Calcular estadísticas del nivel actual
        ejercicios_nivel_actual = [e for e in ejercicios_filtrados if e['nivel_dificultad'] == nivel_actual and not e['bloqueado']]
        completados_nivel = len([e for e in ejercicios_nivel_actual if e['rendimiento_actual'] >= 0.7])
        total_nivel = len(ejercicios_nivel_actual)
        progreso_nivel = (completados_nivel / total_nivel * 100) if total_nivel > 0 else 0
        
        # Estadísticas generales
        total_ejercicios = len(ejercicios_filtrados)
        completados = len([e for e in ejercicios_filtrados if e['rendimiento_actual'] >= 0.7])
        en_progreso = len([e for e in ejercicios_filtrados if 0 < e['rendimiento_actual'] < 0.7])
        bloqueados = len([e for e in ejercicios_filtrados if e['bloqueado']])
        
        siguiente_nivel = orden_niveles[nivel_actual_idx + 1] if nivel_actual_idx + 1 < len(orden_niveles) else None
        
        return {
            "status": "success",
            "nivel_actual": nivel_actual,
            "nivel_numero": nivel_actual_idx + 1,
            "progreso_nivel": progreso_nivel,
            "siguiente_nivel": siguiente_nivel,
            "ejercicios": ejercicios_filtrados,
            "estadisticas": {
                "total": total_ejercicios,
                "completados": completados,
                "en_progreso": en_progreso,
                "bloqueados": bloqueados
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo ejercicios por nivel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
def _calcular_nivel_adaptativo(id_nino: int, id_ejercicio: int) -> str:
    """Calcula el nivel recomendado basado en los últimos 5 intentos."""
    try:
        with db_admin.obtener_conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener últimos 5 puntajes
            cursor.execute("""
                SELECT puntaje_obtenido
                FROM progreso_nino
                WHERE id_nino = %s AND id_ejercicio = %s
                ORDER BY fecha_realizacion DESC
                LIMIT 5
            """, (id_nino, id_ejercicio))
            
            puntajes = [p['puntaje_obtenido'] for p in cursor.fetchall()]
            
            if not puntajes:
                return "Bajo"
            
            promedio = sum(puntajes) / len(puntajes)
            
            if promedio >= 0.7:
                return "Alto"
            elif promedio >= 0.4:
                return "Medio"
            else:
                return "Bajo"
                
    except Exception as e:
        logger.error(f"Error calculando nivel adaptativo: {e}")
        return "Medio"
    
