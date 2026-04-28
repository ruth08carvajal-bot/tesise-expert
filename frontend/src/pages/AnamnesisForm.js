import React, { useState, useEffect } from 'react';

const AnamnesisForm = ({ id_nino, nombre, onFinish }) => {
    const [preguntas, setPreguntas] = useState([]);
    const [edad, setEdad] = useState(0);
    const [nombreNino, setNombreNino] = useState(nombre || 'Niño');
    const [respuestas, setRespuestas] = useState({});
    const [loading, setLoading] = useState(true);
    const [mensaje, setMensaje] = useState('');
    const [progreso, setProgreso] = useState(0);

    useEffect(() => {
        const cargarPreguntas = async () => {
            if (!id_nino) {
                setPreguntas([]);
                setLoading(false);
                setMensaje('No se proporcionó el niño para la anamnesis.');
                return;
            }

            setLoading(true);
            setMensaje('');

            console.log('Cargando preguntas para niño:', id_nino);
            try {
                const response = await fetch(`http://127.0.0.1:8003/anamnesis/preguntas-anamnesis/${id_nino}`);
                console.log('Response status:', response.status);
                if (!response.ok) {
                    const errorBody = await response.text();
                    console.error('Error body:', errorBody);
                    throw new Error(`HTTP ${response.status}: ${errorBody}`);
                }
                const data = await response.json();
                console.log('Data received:', data);
                setPreguntas(data.preguntas || []);
                setEdad(data.edad_nino || 0);
                setNombreNino(data.nombre_nino || nombre || 'Niño');
            } catch (error) {
                console.error('Error cargando preguntas:', error);
                setMensaje('Error al cargar las preguntas. Intenta de nuevo.');
            } finally {
                setLoading(false);
            }
        };

        cargarPreguntas();
    }, [id_nino, nombre]);

    // Actualizar progreso cuando cambian las respuestas
    useEffect(() => {
        const respondidas = Object.keys(respuestas).length;
        const total = preguntas.length;
        setProgreso(total > 0 ? (respondidas / total) * 100 : 0);
    }, [respuestas, preguntas]);

    const handleOptionChange = (id_hecho, valor) => {
        setRespuestas({ ...respuestas, [id_hecho]: valor });
    };

    const guardarAnamnesis = async () => {
        const preguntasSinResponder = preguntas.filter(p => respuestas[p.id_hecho] === undefined);
        if (preguntasSinResponder.length > 0) {
            alert(`Debes responder todas las preguntas antes de guardar. Faltan ${preguntasSinResponder.length} preguntas.`);
            return;
        }

        const hechos_presentes = preguntas
            .filter(p => respuestas[p.id_hecho] === 1)
            .map(p => p.id_hecho);

        const payload = {
            id_nino,
            hechos_presentes
        };

        try {
            const response = await fetch('http://127.0.0.1:8003/anamnesis/guardar-anamnesis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error('Error al guardar la anamnesis');
            }

            await response.json();
            onFinish();
        } catch (error) {
            console.error('Error:', error);
            setMensaje('Hubo un error al guardar la anamnesis. Inténtalo de nuevo.');
        }
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.loadingContainer}>
                    <div style={styles.spinner}></div>
                    <p>Cargando preguntas...</p>
                </div>
            </div>
        );
    }

    if (!id_nino) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.content}>
                    <button style={styles.backButton} onClick={onFinish}>← Volver</button>
                    <div style={styles.errorCard}>
                        <p>No se encontró el niño seleccionado. Vuelve al dashboard y elige un niño válido.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Fondo de imagen */}
            <div style={styles.backgroundImage} />
            
            {/* Contenido */}
            <div style={styles.content}>
                <button style={styles.backButton} onClick={onFinish}>← Volver</button>
                
                <div style={styles.header}>
                    <h1 style={styles.title}>📋 Anamnesis</h1>
                    <p style={styles.subtitle}>Paciente: {nombreNino} | Edad: {edad} años</p>
                </div>

                {/* Barra de progreso */}
                <div style={styles.progressSection}>
                    <div style={styles.progressBarContainer}>
                        <div style={{ ...styles.progressBarFill, width: `${progreso}%` }} />
                    </div>
                    <p style={styles.progressText}>{Math.round(progreso)}% completado</p>
                </div>

                {mensaje && (
                    <div style={styles.errorMessage}>{mensaje}</div>
                )}

                {preguntas.length === 0 ? (
                    <div style={styles.emptyCard}>
                        <p>No hay preguntas disponibles para este niño en este momento.</p>
                    </div>
                ) : (
                    <>
                        <div style={styles.preguntasContainer}>
                            {preguntas.map(p => (
                                <div key={p.id_hecho} style={styles.preguntaCard}>
                                    <div style={styles.preguntaContent}>
                                        <p style={styles.questionText}>{p.descripcion_hecho}</p>
                                        <p style={styles.category}>📂 {p.categoria}</p>
                                    </div>
                                    <div style={styles.options}>
                                        <button
                                            type="button"
                                            onClick={() => handleOptionChange(p.id_hecho, 1)}
                                            style={respuestas[p.id_hecho] === 1 ? styles.btnPresenteActive : styles.btnPresente}
                                        >
                                            ✓ Presente
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => handleOptionChange(p.id_hecho, 0)}
                                            style={respuestas[p.id_hecho] === 0 ? styles.btnAusenteActive : styles.btnAusente}
                                        >
                                            ✗ Ausente
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div style={styles.actions}>
                            <button onClick={guardarAnamnesis} style={styles.saveButton}>
                                Guardar y Finalizar
                            </button>
                            <button onClick={onFinish} style={styles.cancelButton}>
                                Cancelar
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

const styles = {
    container: {
        position: 'relative',
        minHeight: '100vh',
        overflowY: 'auto'
    },
    backgroundImage: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'url("/images/anamnesis.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        zIndex: 0
    },
    content: {
        position: 'relative',
        zIndex: 1,
        maxWidth: '800px',
        margin: '0 30px 0 auto',
        padding: '20px',
        backgroundColor: 'rgba(255, 255, 255, 0.71)',
        borderRadius: '20px',
        minHeight: '100vh'
    },
    backButton: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '20px',
        cursor: 'pointer',
        marginBottom: '20px',
        fontSize: '13px'
    },
    header: {
        textAlign: 'center',
        marginBottom: '25px'
    },
    title: {
        fontSize: '28px',
        color: '#2c3e50',
        margin: '0 0 8px'
    },
    subtitle: {
        fontSize: '14px',
        color: '#363838',
        margin: 0
    },
    progressSection: {
        marginBottom: '25px'
    },
    progressBarContainer: {
        backgroundColor: '#e0e0e0',
        borderRadius: '10px',
        height: '8px',
        overflow: 'hidden'
    },
    progressBarFill: {
        backgroundColor: '#27ae60',
        height: '100%',
        borderRadius: '10px',
        transition: 'width 0.3s ease'
    },
    progressText: {
        fontSize: '12px',
        color: '#404243',
        marginTop: '8px',
        textAlign: 'center'
    },
    errorMessage: {
        backgroundColor: '#f8d7da',
        color: '#721c24',
        padding: '12px',
        borderRadius: '10px',
        marginBottom: '20px',
        textAlign: 'center'
    },
    preguntasContainer: {
        display: 'flex',
        flexDirection: 'column',
        gap: '15px',
        marginBottom: '25px',
        maxHeight: '60vh',
        overflowY: 'auto',
        paddingRight: '5px'
    },
    preguntaCard: {
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '15px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        borderLeft: '4px solid #3498db'
    },
    preguntaContent: {
        flex: 1
    },
    questionText: {
        fontSize: '15px',
        fontWeight: '500',
        color: '#2c3e50',
        margin: '0 0 5px'
    },
    category: {
        fontSize: '12px',
        color: '#7f8c8d',
        margin: 0
    },
    options: {
        display: 'flex',
        gap: '10px'
    },
    btnPresente: {
        backgroundColor: '#f8f9fa',
        color: '#27ae60',
        border: '1px solid #27ae60',
        padding: '8px 16px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500'
    },
    btnPresenteActive: {
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500'
    },
    btnAusente: {
        backgroundColor: '#f8f9fa',
        color: '#e74c3c',
        border: '1px solid #e74c3c',
        padding: '8px 16px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500'
    },
    btnAusenteActive: {
        backgroundColor: '#e74c3c',
        color: 'white',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500'
    },
    actions: {
        display: 'flex',
        gap: '15px',
        justifyContent: 'center',
        marginTop: '10px'
    },
    saveButton: {
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        padding: '12px 24px',
        borderRadius: '30px',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold'
    },
    cancelButton: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '12px 24px',
        borderRadius: '30px',
        cursor: 'pointer',
        fontSize: '14px'
    },
    loadingContainer: {
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'rgba(255,255,255,0.9)'
    },
    spinner: {
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #2c3e50',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite',
        marginBottom: '15px'
    },
    emptyCard: {
        textAlign: 'center',
        padding: '40px',
        backgroundColor: 'white',
        borderRadius: '12px',
        color: '#7f8c8d'
    },
    errorCard: {
        textAlign: 'center',
        padding: '40px',
        backgroundColor: 'white',
        borderRadius: '12px',
        color: '#e74c3c'
    }
};

// Añadir keyframes
const styleSheet = document.createElement("style");
styleSheet.textContent = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(styleSheet);

export default AnamnesisForm;