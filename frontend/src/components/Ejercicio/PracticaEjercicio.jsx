import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_URL_EVALUACION = 'http://127.0.0.1:8003/evaluacion';
const API_URL_EJERCICIOS = 'http://127.0.0.1:8003/ejercicios';

const PracticaEjercicio = ({ ejercicio, idNino, onGuardarProgreso, onVolver }) => {
    const [grabando, setGrabando] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [tiempoInicio, setTiempoInicio] = useState(null);
    const [idEvaluacionPractica, setIdEvaluacionPractica] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [opcionSeleccionada, setOpcionSeleccionada] = useState(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    // Obtener sesión de práctica al cargar
    useEffect(() => {
        const obtenerSesionPractica = async () => {
            try {
                const response = await axios.get(`${API_URL_EJERCICIOS}/sesion-practica/${idNino}`);
                if (response.data.status === 'success') {
                    setIdEvaluacionPractica(response.data.id_evaluacion);
                }
            } catch (error) {
                console.error('Error obteniendo sesión de práctica:', error);
            } finally {
                setCargando(false);
            }
        };
        
        obtenerSesionPractica();
    }, [idNino]);

    // =========================================================
    // TIPO MFCC (Grabación de audio)
    // =========================================================
    const iniciarGrabacion = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'grabacion.webm');
                formData.append('id_nino', idNino);
                formData.append('id_evaluacion', idEvaluacionPractica);
                
                // Convertir el id_hecho_objetivo a nombre de fonema
                const fonemaNombre = mapearIdAFonema(ejercicio.id_hecho_objetivo);
                formData.append('fonema_objetivo', fonemaNombre);

                const tiempoTranscurrido = Math.floor((Date.now() - tiempoInicio) / 1000);

                try {
                    const response = await axios.post(`${API_URL_EVALUACION}/evaluar-fonema`, formData, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    
                    const similitud = response.data.similitud_detectada;
                    setResultado(similitud);
                    onGuardarProgreso(ejercicio.id_ejercicio, similitud, tiempoTranscurrido);
                    
                } catch (error) {
                    console.error('Error evaluando:', error);
                    alert('Error al procesar el audio. Intenta nuevamente.');
                }
                
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setGrabando(true);
            setTiempoInicio(Date.now());
            setResultado(null);

        } catch (err) {
            console.error('Error accediendo al micrófono:', err);
            alert('No se pudo acceder al micrófono. Verifica los permisos.');
        }
    };

    const detenerGrabacion = () => {
        if (mediaRecorderRef.current && grabando) {
            mediaRecorderRef.current.stop();
            setGrabando(false);
        }
    };

    // =========================================================
    // TIPO SELECCIÓN (Opción múltiple)
    // =========================================================
    const manejarSeleccion = (opcion, esCorrecta) => {
        setOpcionSeleccionada(opcion);
        const puntaje = esCorrecta ? 1.0 : 0.0;
        setResultado(puntaje);
        onGuardarProgreso(ejercicio.id_ejercicio, puntaje, 5); // Tiempo estimado 5 segundos
    };

    // =========================================================
    // Helper: Mapear ID de hecho a nombre de fonema
    // =========================================================
    const mapearIdAFonema = (idHecho) => {
        const mapeo = {
            1: 'r', 2: 'rr', 3: 's', 4: 'l', 5: 'c',
            6: 't', 7: 'd', 8: 'p', 9: 'b', 10: 'g',
            14: 'f', 16: 'ch'
        };
        return mapeo[idHecho] || 'r';
    };

    const obtenerMensajeFeedback = (puntaje) => {
        if (puntaje >= 0.7) return "🎉 ¡Excelente! Sigue así.";
        if (puntaje >= 0.4) return "😊 Buen intento. ¡Sigue practicando!";
        return "💪 No te rindas. ¡Sigue intentando!";
    };

    if (cargando) {
        return (
            <div style={styles.container}>
                <button style={styles.backButton} onClick={onVolver}>⬅ Volver</button>
                <div style={styles.card}>
                    <p>Cargando ejercicio...</p>
                </div>
            </div>
        );
    }

    // =========================================================
    // RENDERIZADO SEGÚN TIPO DE EJERCICIO
    // =========================================================
    const esTipoMFCC = ejercicio.tipo_apoyo === 'MFCC';
    const esTipoSeleccion = ejercicio.tipo_apoyo === 'Selección';
    const esTipoFuzzy = ejercicio.tipo_apoyo === 'Fuzzy-Padre';

    const opcionesDeSeleccion = ejercicio.opciones || [
        { id: 'A', texto: 'Opción A', correcta: true },
        { id: 'B', texto: 'Opción B', correcta: false },
        { id: 'C', texto: 'Opción C', correcta: false }
    ];

    const imagenEjercicio = ejercicio.imagen || ejercicio.imagen_recurso;

    return (
        <div style={styles.container}>
            <button style={styles.backButton} onClick={onVolver}>
                ⬅ Volver a mis ejercicios
            </button>

            <div style={styles.card}>
                <div style={styles.headerCard}>
                    <div style={styles.headerText}>
                        <h2 style={styles.title}>{ejercicio.nombre}</h2>
                        <p style={styles.description}>{ejercicio.descripcion}</p>
                    </div>
                    <div style={styles.gameBadgeRow}>
                        <span style={styles.badge}>{ejercicio.tipo_apoyo || 'Actividad'}</span>
                        <span style={styles.badgeSecondary}>{ejercicio.nivel || 'Nivel Básico'}</span>
                    </div>
                </div>

                {imagenEjercicio ? (
                    <div style={styles.imageWrapper}>
                        <img src={imagenEjercicio} alt={ejercicio.nombre} style={styles.exerciseImage} />
                    </div>
                ) : (
                    <div style={styles.imageWrapperPlaceholder}>
                        <span style={styles.placeholderLabel}>Imagen del juego</span>
                    </div>
                )}

                {/* TIPO MFCC: Grabación de voz */}
                {esTipoMFCC && (
                    <div style={styles.practiceArea}>
                        <p style={styles.instructions}>
                            Habla con claridad la palabra indicada y luego presiona detener para evaluar tu pronunciación.
                        </p>
                        {!grabando ? (
                            <button style={styles.recordButton} onClick={iniciarGrabacion}>
                                🎤 Iniciar Práctica
                            </button>
                        ) : (
                            <button style={styles.stopButton} onClick={detenerGrabacion}>
                                🛑 Detener y Evaluar
                            </button>
                        )}
                        {grabando && <p style={styles.recordingText}>Grabando... ¡Habla ahora! 🎧</p>}
                    </div>
                )}

                {/* TIPO SELECCIÓN: Opción múltiple */}
                {esTipoSeleccion && (
                    <div style={styles.practiceArea}>
                        <p style={styles.preguntaSeleccion}>
                            {ejercicio.pregunta || 'Selecciona la respuesta correcta:'}
                        </p>
                        <div style={styles.opcionesContainer}>
                            {opcionesDeSeleccion.map((opcion) => (
                                <button
                                    key={opcion.id}
                                    style={{
                                        ...styles.opcionButton,
                                        ...(opcionSeleccionada === opcion.id ? styles.opcionButtonActive : {})
                                    }}
                                    onClick={() => manejarSeleccion(opcion.id, opcion.correcta)}
                                >
                                    {opcion.texto}
                                </button>
                            ))}
                        </div>
                        {opcionSeleccionada && (
                            <p style={styles.seleccionInfo}>Seleccionaste: {opcionSeleccionada}</p>
                        )}
                    </div>
                )}

                {/* TIPO FUZZY: Auto-evaluación del niño */}
                {esTipoFuzzy && (
                    <div style={styles.practiceArea}>
                        <p style={styles.infoFuzzy}>
                            Practica este ejercicio mientras revisas la imagen y luego marca si lo completaste.
                        </p>
                        <button style={styles.simularButton} onClick={() => manejarSeleccion('Practica', true)}>
                            ✅ Marcar como completado
                        </button>
                    </div>
                )}

                {/* Resultado después de practicar */}
                {resultado !== null && (
                    <div style={styles.resultContainer}>
                        <div style={styles.resultBadge(resultado)}>
                            {resultado >= 0.7 ? '✅' : resultado >= 0.4 ? '📈' : '🔄'}
                            {' '}{Math.round(resultado * 100)}%
                        </div>
                        <p style={styles.feedback}>{obtenerMensajeFeedback(resultado)}</p>
                        <button style={styles.tryAgainButton} onClick={() => {
                            setResultado(null);
                            setOpcionSeleccionada(null);
                        }}>
                            🔁 Practicar de nuevo
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const styles = {
    container: {
        minHeight: '100vh',
        backgroundColor: '#f0f4f8',
        padding: '40px'
    },
    backButton: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '8px',
        cursor: 'pointer',
        marginBottom: '20px'
    },
    card: {
        backgroundColor: 'white',
        borderRadius: '24px',
        padding: '36px',
        maxWidth: '720px',
        margin: '0 auto',
        textAlign: 'center',
        boxShadow: '0 18px 40px rgba(0,0,0,0.08)'
    },
    headerCard: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '20px',
        marginBottom: '24px',
        flexWrap: 'wrap'
    },
    headerText: {
        textAlign: 'left',
        flex: 1,
        minWidth: '220px'
    },
    gameBadgeRow: {
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        alignItems: 'flex-end'
    },
    badge: {
        backgroundColor: '#27ae60',
        color: 'white',
        padding: '8px 16px',
        borderRadius: '999px',
        fontSize: '12px',
        fontWeight: '700'
    },
    badgeSecondary: {
        backgroundColor: '#ecf0f1',
        color: '#2c3e50',
        padding: '8px 16px',
        borderRadius: '999px',
        fontSize: '12px',
        fontWeight: '700'
    },
    description: {
        color: '#555',
        fontSize: '16px',
        lineHeight: '1.7',
        marginBottom: '0'
    },
    imageWrapper: {
        marginTop: '24px',
        marginBottom: '24px',
        borderRadius: '24px',
        overflow: 'hidden',
        boxShadow: '0 16px 30px rgba(0,0,0,0.08)'
    },
    imageWrapperPlaceholder: {
        marginTop: '24px',
        marginBottom: '24px',
        borderRadius: '24px',
        minHeight: '240px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f7fa',
        boxShadow: '0 12px 24px rgba(0,0,0,0.05)'
    },
    exerciseImage: {
        width: '100%',
        height: 'auto',
        display: 'block'
    },
    placeholderLabel: {
        color: '#95a5a6',
        fontSize: '16px'
    },
    practiceArea: {
        margin: '30px 0'
    },
    instructions: {
        fontSize: '15px',
        color: '#4b6584',
        marginBottom: '20px',
        maxWidth: '650px',
        marginLeft: 'auto',
        marginRight: 'auto'
    },
    recordingText: {
        marginTop: '16px',
        color: '#e74c3c',
        fontWeight: '700'
    },
    recordButton: {
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        padding: '15px 30px',
        borderRadius: '50px',
        fontSize: '18px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    stopButton: {
        backgroundColor: '#e74c3c',
        color: 'white',
        border: 'none',
        padding: '15px 30px',
        borderRadius: '50px',
        fontSize: '18px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    preguntaSeleccion: {
        fontSize: '18px',
        marginBottom: '20px',
        color: '#2c3e50'
    },
    stopButton: {
        backgroundColor: '#e74c3c',
        color: 'white',
        border: 'none',
        padding: '15px 30px',
        borderRadius: '50px',
        fontSize: '18px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    preguntaSeleccion: {
        fontSize: '18px',
        marginBottom: '20px',
        color: '#2c3e50'
    },
    opcionesContainer: {
        display: 'flex',
        gap: '15px',
        justifyContent: 'center',
        flexWrap: 'wrap'
    },
    opcionButton: {
        backgroundColor: '#3498db',
        color: 'white',
        border: 'none',
        padding: '14px 26px',
        borderRadius: '14px',
        cursor: 'pointer',
        fontSize: '16px',
        minWidth: '160px',
        transition: 'transform 0.18s ease, background-color 0.18s ease'
    },
    opcionButtonActive: {
        backgroundColor: '#2c3e50'
    },
    seleccionInfo: {
        marginTop: '15px',
        color: '#7f8c8d'
    },
    infoFuzzy: {
        fontSize: '16px',
        color: '#555',
        marginBottom: '20px'
    },
    simularButton: {
        backgroundColor: '#f39c12',
        color: 'white',
        border: 'none',
        padding: '12px 25px',
        borderRadius: '10px',
        cursor: 'pointer',
        fontSize: '16px'
    },
    resultContainer: {
        marginTop: '30px',
        padding: '20px',
        backgroundColor: '#f8f9fa',
        borderRadius: '15px'
    },
    resultBadge: (puntaje) => ({
        fontSize: '48px',
        fontWeight: 'bold',
        color: puntaje >= 0.7 ? '#27ae60' : puntaje >= 0.4 ? '#f39c12' : '#e74c3c',
        marginBottom: '10px'
    }),
    feedback: {
        fontSize: '16px',
        color: '#555',
        marginBottom: '20px'
    },
    tryAgainButton: {
        backgroundColor: '#3498db',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '8px',
        cursor: 'pointer'
    }
};

export default PracticaEjercicio;