import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import GlosarioModal from '../Glosario/GlosarioModal';

const API_URL = 'http://127.0.0.1:8003/explicacion';

const ModuloExplicativo = ({ idNino, idEvaluacion, nombreNino, onClose }) => {
    const [pregunta, setPregunta] = useState('');
    const [cargando, setCargando] = useState(false);
    const [sugerencias, setSugerencias] = useState([]);
    const [historial, setHistorial] = useState([]);
    const [mostrarGlosario, setMostrarGlosario] = useState(false);

    const preguntasPredefinidas = [
        "¿Qué dificultades tiene mi hijo?",
        "¿Qué ejercicios me recomiendas?",
        "¿Cómo va su progreso?",
        "¿Cómo motivarlo?"
    ];

    const enviarPregunta = async (preguntaTexto = pregunta) => {
        if (!preguntaTexto.trim()) return;

        const nuevaPregunta = { rol: 'tutor', texto: preguntaTexto };
        setHistorial(prev => [...prev, nuevaPregunta]);
        setPregunta('');
        setCargando(true);

        try {
            const response = await axios.post(`${API_URL}/chat`, {
                id_nino: idNino,
                id_evaluacion: idEvaluacion,
                mensaje: preguntaTexto
            });

            const nuevaRespuesta = {
                rol: 'sistema',
                texto: response.data.respuesta
            };
            
            setHistorial(prev => [...prev, nuevaRespuesta]);
            setSugerencias(response.data.sugerencias || []);

        } catch (error) {
            console.error('Error:', error);
            setHistorial(prev => [...prev, {
                rol: 'sistema',
                texto: 'Lo siento, hubo un error al procesar tu pregunta. Por favor, intenta de nuevo.'
            }]);
        } finally {
            setCargando(false);
        }
    };

    return (
        <>
            {/* Modal overlay con imagen de fondo */}
            <div style={styles.modalOverlay} onClick={onClose}>
                {/* Imagen de fondo */}
                <div style={styles.backgroundImage} />
                
                {/* Contenido del modal */}
                <div style={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
                    {/* Cabecera */}
                    <div style={styles.header}>
                        <div>
                            <h3 style={styles.title}>💬 Asistente Clínico</h3>
                            <p style={styles.subtitle}>Pregunta sobre {nombreNino}</p>
                        </div>
                        <div style={styles.headerActions}>
                            <button 
                                style={styles.glosarioButton}
                                onClick={() => setMostrarGlosario(true)}
                            >
                                📖 Glosario
                            </button>
                            <button style={styles.closeButton} onClick={onClose}>✕</button>
                        </div>
                    </div>

                    {/* Historial de conversación */}
                    <div style={styles.historialContainer}>
                        {historial.length === 0 ? (
                            <div style={styles.bienvenida}>
                                <p>🤖 ¡Hola! Soy el asistente clínico.</p>
                                <p>Puedo explicarte:</p>
                                <ul style={styles.listaBienvenida}>
                                    <li>🔬 Los diagnósticos obtenidos</li>
                                    <li>🎯 Los ejercicios recomendados</li>
                                    <li>📊 La confiabilidad de los resultados</li>
                                    <li>📈 El progreso del niño</li>
                                </ul>
                                <p>Haz clic en una pregunta o escribe la tuya:</p>
                            </div>
                        ) : (
                            historial.map((item, idx) => (
                                <div key={idx} style={item.rol === 'tutor' ? styles.mensajeTutor : styles.mensajeSistema}>
                                    <div style={styles.mensajeBurbuja(item.rol)}>
                                        <strong>{item.rol === 'tutor' ? '👨‍👩‍👧 Usted:' : '🤖 Asistente:'}</strong>
                                        <div style={styles.mensajeTexto}>
                                            <ReactMarkdown>{item.texto}</ReactMarkdown>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                        
                        {cargando && (
                            <div style={styles.mensajeSistema}>
                                <div style={styles.mensajeBurbuja('sistema')}>
                                    <p style={styles.mensajeTexto}>✍️ Escribiendo...</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Sugerencias */}
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

                    {/* Input */}
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
                            📤
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

            {mostrarGlosario && (
                <GlosarioModal onClose={() => setMostrarGlosario(false)} />
            )}
        </>
    );
};

const styles = {
    modalOverlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000
    },
    backgroundImage: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'url("/images/fondo_chat.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        zIndex: 0
    },
    modalContainer: {
        position: 'relative',
        backgroundColor: 'rgba(170, 238, 234, 0.29)',
        borderRadius: '20px',
        width: '90%',
        maxWidth: '650px',
        height: '85vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
        zIndex: 1
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 20px',
        backgroundColor: '#2c3e50',
        color: 'white'
    },
    headerActions: {
        display: 'flex',
        gap: '10px',
        alignItems: 'center'
    },
    title: {
        margin: 0,
        fontSize: '18px'
    },
    subtitle: {
        margin: '4px 0 0',
        fontSize: '12px',
        opacity: 0.8
    },
    glosarioButton: {
        backgroundColor: 'rgba(255,255,255,0.2)',
        border: 'none',
        padding: '6px 12px',
        borderRadius: '20px',
        color: 'white',
        cursor: 'pointer',
        fontSize: '12px'
    },
    closeButton: {
        background: 'none',
        border: 'none',
        color: 'white',
        fontSize: '22px',
        cursor: 'pointer',
        padding: '0 5px'
    },
    historialContainer: {
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        backgroundColor: 'rgba(255, 255, 255, 0.85)'
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
        maxWidth: '85%',
        padding: '10px 14px',
        borderRadius: '18px',
        backgroundColor: rol === 'tutor' ? '#2c3e50' : '#e9ecef',
        color: rol === 'tutor' ? 'white' : '#333'
    }),
    mensajeTexto: {
        fontSize: '14px',
        lineHeight: '1.5',
        wordBreak: 'break-word'
    },
    sugerenciasContainer: {
        padding: '12px 16px',
        borderTop: '1px solid #dee2e6',
        backgroundColor: 'rgba(255, 255, 255, 0.9)'
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
        backgroundColor: 'rgba(255, 255, 255, 0.9)'
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
        padding: '10px 18px',
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '24px',
        cursor: 'pointer',
        fontSize: '16px'
    },
    rapidosContainer: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        padding: '12px 16px',
        borderTop: '1px solid #dee2e6',
        backgroundColor: 'rgba(255, 255, 255, 0.9)'
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