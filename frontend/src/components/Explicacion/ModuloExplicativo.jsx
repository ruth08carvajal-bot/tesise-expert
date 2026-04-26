import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8003/explicacion';

const ModuloExplicativo = ({ idNino, idEvaluacion, nombreNino, onClose }) => {
    const [pregunta, setPregunta] = useState('');
    const [cargando, setCargando] = useState(false);
    const [sugerencias, setSugerencias] = useState([]);
    const [historial, setHistorial] = useState([]);

    const preguntasPredefinidas = [
        "¿Qué diagnósticos tiene mi hijo?",
        "¿Por qué se recomiendan estos ejercicios?",
        "¿Qué significan los puntajes de audio?",
        "¿Qué tan seguro es este diagnóstico?"
    ];

    const enviarPregunta = async (preguntaTexto = pregunta) => {
        if (!preguntaTexto.trim()) return;

        // Añadir al historial
        const nuevaPregunta = { rol: 'tutor', texto: preguntaTexto };
        setHistorial(prev => [...prev, nuevaPregunta]);
        setPregunta('');
        setCargando(true);

        try {
            const response = await axios.post(`${API_URL}/explicar`, {
                id_nino: idNino,
                id_evaluacion: idEvaluacion,
                pregunta: preguntaTexto
            });

            const nuevaRespuesta = {
                rol: 'sistema',
                texto: response.data.respuesta,
                hechos_activados: response.data.hechos_activados || []
            };
            
            setHistorial(prev => [...prev, nuevaRespuesta]);
            setSugerencias(response.data.sugerencias || []);

        } catch (error) {
            console.error('Error en módulo explicativo:', error);
            setHistorial(prev => [...prev, {
                rol: 'sistema',
                texto: 'Lo siento, hubo un error al procesar tu pregunta. Por favor, intenta de nuevo.'
            }]);
        } finally {
            setCargando(false);
        }
    };

    return (
        <div style={styles.modalOverlay} onClick={onClose}>
            <div style={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
                {/* Cabecera */}
                <div style={styles.header}>
                    <div>
                        <h3 style={styles.title}>💬 Módulo Explicativo</h3>
                        <p style={styles.subtitle}>Pregunta sobre el diagnóstico de {nombreNino}</p>
                    </div>
                    <button style={styles.closeButton} onClick={onClose}>✕</button>
                </div>

                {/* Historial de conversación */}
                <div style={styles.historialContainer}>
                    {historial.length === 0 ? (
                        <div style={styles.bienvenida}>
                            <p>🤖 ¡Hola! Soy el asistente clínico.</p>
                            <p>Puedo explicarte:</p>
                            <ul style={styles.listaBienvenida}>
                                <li>🔬 Los diagnósticos obtenidos</li>
                                <li>🎯 Por qué se recomiendan ciertos ejercicios</li>
                                <li>🎙️ El significado de los puntajes MFCC</li>
                                <li>📊 La confiabilidad de los resultados</li>
                            </ul>
                            <p>Haz clic en una pregunta sugerida o escribe la tuya:</p>
                        </div>
                    ) : (
                        historial.map((item, idx) => (
                            <div key={idx} style={item.rol === 'tutor' ? styles.mensajeTutor : styles.mensajeSistema}>
                                <div style={styles.mensajeBurbuja(item.rol)}>
                                    <strong>{item.rol === 'tutor' ? '👨‍👩‍👧 Usted:' : '🤖 Asistente:'}</strong>
                                    <p style={styles.mensajeTexto}>{item.texto}</p>
                                </div>
                            </div>
                        ))
                    )}
                    
                    {cargando && (
                        <div style={styles.mensajeSistema}>
                            <div style={styles.mensajeBurbuja('sistema')}>
                                <p style={styles.mensajeTexto}>⚙️ Analizando...</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Preguntas sugeridas */}
                {sugerencias.length > 0 && (
                    <div style={styles.sugerenciasContainer}>
                        <p style={styles.sugerenciasLabel}>💡 También puedes preguntar:</p>
                        <div style={styles.sugerenciasLista}>
                            {sugerencias.map((sug, idx) => (
                                <button
                                    key={idx}
                                    style={styles.sugerenciaBoton}
                                    onClick={() => enviarPregunta(sug)}
                                >
                                    {sug}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Área de entrada */}
                <div style={styles.inputArea}>
                    <input
                        type="text"
                        style={styles.input}
                        placeholder="Escribe tu pregunta aquí..."
                        value={pregunta}
                        onChange={(e) => setPregunta(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && enviarPregunta()}
                        disabled={cargando}
                    />
                    <button
                        style={styles.enviarButton}
                        onClick={() => enviarPregunta()}
                        disabled={cargando || !pregunta.trim()}
                    >
                        📤 Enviar
                    </button>
                </div>

                {/* Botones rápidos */}
                <div style={styles.rapidosContainer}>
                    {preguntasPredefinidas.map((p, idx) => (
                        <button
                            key={idx}
                            style={styles.rapidoBoton}
                            onClick={() => enviarPregunta(p)}
                            disabled={cargando}
                        >
                            {p}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

const styles = {
    modalOverlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000
    },
    modalContainer: {
        backgroundColor: 'white',
        borderRadius: '16px',
        width: '90%',
        maxWidth: '600px',
        height: '80vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 20px',
        borderBottom: '1px solid #e9ecef',
        backgroundColor: '#2c3e50',
        borderRadius: '16px 16px 0 0',
        color: 'white'
    },
    title: {
        margin: 0,
        fontSize: '18px'
    },
    subtitle: {
        margin: '5px 0 0',
        fontSize: '12px',
        opacity: 0.8
    },
    closeButton: {
        background: 'none',
        border: 'none',
        color: 'white',
        fontSize: '20px',
        cursor: 'pointer',
        padding: '5px'
    },
    historialContainer: {
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        backgroundColor: '#f8f9fa'
    },
    bienvenida: {
        textAlign: 'center',
        padding: '20px',
        color: '#555'
    },
    listaBienvenida: {
        textAlign: 'left',
        margin: '15px 0',
        paddingLeft: '30px'
    },
    mensajeTutor: {
        display: 'flex',
        justifyContent: 'flex-end',
        marginBottom: '12px'
    },
    mensajeSistema: {
        display: 'flex',
        justifyContent: 'flex-start',
        marginBottom: '12px'
    },
    mensajeBurbuja: (rol) => ({
        maxWidth: '80%',
        padding: '10px 14px',
        borderRadius: '18px',
        backgroundColor: rol === 'tutor' ? '#2c3e50' : '#e9ecef',
        color: rol === 'tutor' ? 'white' : '#333'
    }),
    mensajeTexto: {
        margin: '5px 0 0',
        fontSize: '14px',
        lineHeight: '1.4'
    },
    sugerenciasContainer: {
        padding: '12px 16px',
        borderTop: '1px solid #dee2e6',
        backgroundColor: '#f8f9fa'
    },
    sugerenciasLabel: {
        margin: '0 0 8px 0',
        fontSize: '12px',
        color: '#6c757d'
    },
    sugerenciasLista: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px'
    },
    sugerenciaBoton: {
        backgroundColor: '#e9ecef',
        border: 'none',
        padding: '6px 12px',
        borderRadius: '20px',
        fontSize: '12px',
        cursor: 'pointer',
        color: '#2c3e50'
    },
    inputArea: {
        display: 'flex',
        padding: '12px 16px',
        borderTop: '1px solid #dee2e6',
        gap: '10px',
        backgroundColor: 'white'
    },
    input: {
        flex: 1,
        padding: '10px 14px',
        border: '1px solid #ced4da',
        borderRadius: '24px',
        fontSize: '14px',
        outline: 'none'
    },
    enviarButton: {
        padding: '10px 20px',
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '24px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    rapidosContainer: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        padding: '12px 16px',
        borderTop: '1px solid #dee2e6',
        backgroundColor: '#f8f9fa'
    },
    rapidoBoton: {
        backgroundColor: '#e8f4fd',
        border: '1px solid #3498db',
        padding: '6px 12px',
        borderRadius: '20px',
        fontSize: '11px',
        cursor: 'pointer',
        color: '#3498db'
    }
};

export default ModuloExplicativo;