import React, { useState, useEffect } from 'react';
import EvaluacionFonetica from '../components/Evaluacion/EvaluacionFonetica';
import { iniciarEvaluacion } from '../api/evaluacionService';

const EvaluacionPage = ({ idNino, onBack }) => {
    const [idEvaluacion, setIdEvaluacion] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [nombreNino, setNombreNino] = useState('');

    useEffect(() => {
        const iniciarSesionEvaluacion = async () => {
            if (!idNino) {
                setError('No se ha seleccionado ningún niño');
                setLoading(false);
                return;
            }

            try {
                // Obtener nombre del niño
                try {
                    const ninoResponse = await fetch(`http://127.0.0.1:8003/ninos/nino/${idNino}`);
                    if (ninoResponse.ok) {
                        const nino = await ninoResponse.json();
                        setNombreNino(nino.nombre);
                    }
                } catch (err) {
                    console.error('Error obteniendo nombre:', err);
                }

                const response = await iniciarEvaluacion(idNino);
                if (response.status === 'success') {
                    setIdEvaluacion(response.id_evaluacion);
                } else {
                    setError(response.mensaje || 'Error al iniciar la evaluación');
                }
            } catch (error) {
                console.error('Error al iniciar evaluación:', error);
                setError('Error de conexión con el servidor');
            } finally {
                setLoading(false);
            }
        };

        iniciarSesionEvaluacion();
    }, [idNino]);

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.loadingContainer}>
                    <div style={styles.spinner}></div>
                    <p>Preparando la evaluación para {nombreNino || 'el niño'}...</p>
                    <p style={styles.loadingSubtext}>Esto tomará solo unos segundos</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.errorContainer}>
                    <div style={styles.errorIcon}>😅</div>
                    <h2>¡Ups! Algo salió mal</h2>
                    <p>{error}</p>
                    <button style={styles.backButton} onClick={onBack}>
                        ← Volver al inicio
                    </button>
                </div>
            </div>
        );
    }

    if (!idEvaluacion) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.errorContainer}>
                    <div style={styles.errorIcon}>🔍</div>
                    <h2>No se pudo iniciar la evaluación</h2>
                    <p>Hubo un problema al preparar tu evaluación. Por favor, intenta nuevamente.</p>
                    <button style={styles.backButton} onClick={onBack}>
                        ← Volver al inicio
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Fondo de imagen */}
            <div style={styles.backgroundImage} />
            
            {/* Contenido principal */}
            <div style={styles.content}>
                {/* Cabecera */}
                <div style={styles.header}>
                    <button style={styles.closeButton} onClick={onBack} title="Salir de la evaluación">
                        ✕ Salir
                    </button>
                    <div style={styles.headerInfo}>
                        <h1 style={styles.title}>🎤 Evaluación Fonética</h1>
                        <p style={styles.subtitle}>
                            {nombreNino ? `¡Hola, ${nombreNino}!` : '¡Hola!'} Vamos a practicar algunos sonidos
                        </p>
                    </div>
                </div>

                {/* Instrucciones */}
                <div style={styles.instructions}>
                    <div style={styles.instructionItem}>
                        <span style={styles.instructionIcon}>1</span>
                        <span>Presiona el botón 🎤 para comenzar a grabar</span>
                    </div>
                    <div style={styles.instructionItem}>
                        <span style={styles.instructionIcon}>2</span>
                        <span>Dice la palabra en voz alta y clara</span>
                    </div>
                    <div style={styles.instructionItem}>
                        <span style={styles.instructionIcon}>3</span>
                        <span>Presiona 🛑 cuando termines</span>
                    </div>
                </div>

                {/* Evaluación */}
                <div style={styles.evaluacionWrapper}>
                    <EvaluacionFonetica
                        idNino={idNino}
                        idEvaluacion={idEvaluacion}
                        onFinish={onBack}
                    />
                </div>

                {/* Mensaje de apoyo */}
                <p style={styles.supportMessage}>
                    💡 No te preocupes si no sale perfecto, ¡lo importante es intentarlo!
                </p>
            </div>
        </div>
    );
};

const styles = {
    container: {
        position: 'relative',
        minHeight: '100vh',
        overflow: 'hidden'
    },
    backgroundImage: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'url("/images/fondo_progreso.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        zIndex: 0
    },
    content: {
        position: 'relative',
        zIndex: 1,
        maxWidth: '800px',
        margin: '0 auto',
        padding: '20px',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column'
    },
    header: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '25px',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: '15px 25px',
        borderRadius: '20px',
        backdropFilter: 'blur(5px)'
    },
    closeButton: {
        backgroundColor: '#e74c3c',
        color: 'white',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500'
    },
    headerInfo: {
        textAlign: 'center',
        flex: 1
    },
    title: {
        fontSize: '24px',
        color: '#2c3e50',
        margin: 0
    },
    subtitle: {
        fontSize: '14px',
        color: '#7f8c8d',
        margin: '5px 0 0'
    },
    instructions: {
        display: 'flex',
        justifyContent: 'space-between',
        gap: '15px',
        marginBottom: '25px',
        flexWrap: 'wrap'
    },
    instructionItem: {
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        padding: '12px 15px',
        borderRadius: '15px',
        fontSize: '13px',
        color: '#2c3e50',
        backdropFilter: 'blur(5px)'
    },
    instructionIcon: {
        width: '24px',
        height: '24px',
        backgroundColor: '#3498db',
        color: 'white',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '12px',
        fontWeight: 'bold'
    },
    evaluacionWrapper: {
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderRadius: '25px',
        padding: '25px',
        marginBottom: '20px',
        backdropFilter: 'blur(5px)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
    },
    supportMessage: {
        textAlign: 'center',
        fontSize: '12px',
        color: 'rgba(255, 255, 255, 0.9)',
        margin: 0,
        textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
    },
    loadingContainer: {
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        margin: '0 auto',
        maxWidth: '400px',
        borderRadius: '20px',
        textAlign: 'center'
    },
    spinner: {
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        width: '50px',
        height: '50px',
        animation: 'spin 1s linear infinite',
        marginBottom: '20px'
    },
    loadingSubtext: {
        fontSize: '12px',
        color: '#7f8c8d',
        marginTop: '10px'
    },
    errorContainer: {
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        margin: '0 auto',
        maxWidth: '400px',
        borderRadius: '20px',
        textAlign: 'center',
        padding: '30px'
    },
    errorIcon: {
        fontSize: '48px',
        marginBottom: '20px'
    },
    backButton: {
        marginTop: '20px',
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '25px',
        cursor: 'pointer'
    }
};

// Añadir keyframes
const styleSheet = document.createElement("style");
styleSheet.textContent = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(styleSheet);

export default EvaluacionPage;