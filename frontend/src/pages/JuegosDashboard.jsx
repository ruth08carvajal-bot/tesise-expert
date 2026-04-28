import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PracticaEjercicio from '../components/Ejercicio/PracticaEjercicio';
import { API_ENDPOINTS } from '../config';

const JuegosDashboard = ({ idNino, onBack }) => {
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [ejerciciosPorNivel, setEjerciciosPorNivel] = useState({ Bajo: [], Medio: [], Alto: [] });
    const [ejercicioSeleccionado, setEjercicioSeleccionado] = useState(null);
    const [feedback, setFeedback] = useState({ texto: '', tipo: '', mostrar: false });

    useEffect(() => {
        const cargarJuegos = async () => {
            try {
                const response = await axios.get(`${API_ENDPOINTS.ejercicios}/mis-ejercicios/${idNino}`);
                if (response.data.status === 'success') {
                    const ejerciciosRaw = response.data.ejercicios || [];
                    const porNivel = { Bajo: [], Medio: [], Alto: [] };

                    ejerciciosRaw.forEach((ej) => {
                        const nivel = ej.nivel || 'Bajo';
                        if (!porNivel[nivel]) porNivel[nivel] = [];
                        porNivel[nivel].push(ej);
                    });

                    setEjerciciosPorNivel(porNivel);
                } else {
                    setError('No se encontraron juegos disponibles.');
                }
            } catch (err) {
                console.error('Error cargando juegos:', err);
                setError('No se pudieron cargar los juegos. Intenta más tarde.');
            } finally {
                setCargando(false);
            }
        };

        cargarJuegos();
    }, [idNino]);

    const handleEntrarEjercicio = (ejercicio) => {
        setEjercicioSeleccionado(ejercicio);
    };

    const handleGuardarProgreso = async (idEjercicio, puntaje, tiempo) => {
        try {
            await axios.post(`${API_ENDPOINTS.ejercicios}/guardar-progreso`, {
                id_nino: idNino,
                id_ejercicio: idEjercicio,
                puntaje_obtenido: puntaje,
                tiempo_empleado: tiempo
            });

            setFeedback({ texto: '¡Progreso guardado! Sigue jugando.', tipo: 'success', mostrar: true });
            setTimeout(() => setFeedback({ texto: '', tipo: '', mostrar: false }), 3000);
        } catch (err) {
            console.error('Error guardando progreso en juegos:', err);
            setFeedback({ texto: 'No se pudo guardar el progreso. Intenta de nuevo.', tipo: 'error', mostrar: true });
            setTimeout(() => setFeedback({ texto: '', tipo: '', mostrar: false }), 3000);
        }
    };

    const niveles = [
        { key: 'Bajo', nombre: 'Nivel Bajo', color: '#27ae60' },
        { key: 'Medio', nombre: 'Nivel Medio', color: '#3498db' },
        { key: 'Alto', nombre: 'Nivel Alto', color: '#f39c12' }
    ];

    if (cargando) {
        return (
            <div style={styles.container}>
                <button style={styles.backButton} onClick={onBack}>⬅ Volver</button>
                <div style={styles.loadingCard}>Cargando juegos...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.container}>
                <button style={styles.backButton} onClick={onBack}>⬅ Volver</button>
                <div style={styles.errorCard}>{error}</div>
            </div>
        );
    }

    if (ejercicioSeleccionado) {
        return (
            <PracticaEjercicio
                ejercicio={ejercicioSeleccionado}
                idNino={idNino}
                onGuardarProgreso={handleGuardarProgreso}
                onVolver={() => setEjercicioSeleccionado(null)}
            />
        );
    }

    return (
        <div style={styles.container}>
            <div style={styles.toolbar}>
                <button style={styles.backButton} onClick={onBack}>⬅ Volver</button>
                <h1 style={styles.title}>Juegos Propuestos</h1>
            </div>

            <div style={styles.introCard}>
                <p>Estas son las actividades propuestas para ti. Elige un juego y comienza a practicar.</p>
            </div>

            {niveles.map((nivel) => {
                const ejercicios = ejerciciosPorNivel[nivel.key] || [];
                return (
                    <div key={nivel.key} style={{ ...styles.levelSection, borderColor: nivel.color }}>
                        <div style={{ ...styles.levelHeader, backgroundColor: nivel.color }}>
                            <h2 style={styles.levelTitle}>{nivel.nombre}</h2>
                            <span style={styles.levelCount}>{ejercicios.length} juego{ejercicios.length === 1 ? '' : 's'}</span>
                        </div>

                        {ejercicios.length === 0 ? (
                            <div style={styles.emptyLevel}>Completa más ejercicios para desbloquear juegos aquí.</div>
                        ) : (
                            ejercicios.map((ejercicio) => (
                                <div key={ejercicio.id_ejercicio} style={styles.gameCard}>
                                    <div>
                                        <h3 style={styles.gameTitle}>{ejercicio.nombre}</h3>
                                        <p style={styles.gameDescription}>{ejercicio.descripcion}</p>
                                    </div>
                                    <button style={styles.enterButton} onClick={() => handleEntrarEjercicio(ejercicio)}>
                                        Entrar
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                );
            })}

            {feedback.mostrar && (
                <div style={styles.feedbackBubble}>{feedback.texto}</div>
            )}
        </div>
    );
};

const styles = {
    container: {
        minHeight: '100vh',
        backgroundColor: '#eef6fb',
        padding: '20px',
    },
    toolbar: {
        display: 'flex',
        alignItems: 'center',
        gap: '20px',
        marginBottom: '20px',
        flexWrap: 'wrap'
    },
    title: {
        margin: 0,
        fontSize: '24px',
        color: '#2c3e50'
    },
    backButton: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '10px 16px',
        borderRadius: '12px',
        cursor: 'pointer'
    },
    introCard: {
        backgroundColor: 'white',
        borderRadius: '20px',
        padding: '24px',
        boxShadow: '0 10px 24px rgba(0,0,0,0.08)',
        marginBottom: '24px'
    },
    levelSection: {
        border: '2px solid',
        borderRadius: '20px',
        marginBottom: '20px',
        overflow: 'hidden',
        backgroundColor: 'white'
    },
    levelHeader: {
        padding: '16px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
    },
    levelTitle: {
        margin: 0,
        color: 'white',
        fontSize: '18px'
    },
    levelCount: {
        color: 'white',
        fontWeight: '700'
    },
    emptyLevel: {
        padding: '20px',
        color: '#7f8c8d'
    },
    gameCard: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        padding: '18px 20px',
        borderTop: '1px solid #f0f0f0'
    },
    gameTitle: {
        margin: 0,
        fontSize: '16px',
        color: '#2c3e50'
    },
    gameDescription: {
        margin: '8px 0 0',
        color: '#7f8c8d',
        fontSize: '14px',
        maxWidth: '680px'
    },
    enterButton: {
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '14px',
        padding: '12px 18px',
        cursor: 'pointer'
    },
    feedbackBubble: {
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: '#2ecc71',
        color: 'white',
        padding: '14px 24px',
        borderRadius: '30px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.12)'
    },
    loadingCard: {
        marginTop: '40px',
        padding: '24px',
        backgroundColor: 'white',
        borderRadius: '16px',
        boxShadow: '0 10px 24px rgba(0,0,0,0.08)'
    },
    errorCard: {
        marginTop: '40px',
        padding: '24px',
        backgroundColor: '#fdecea',
        borderRadius: '16px',
        color: '#c0392b'
    }
};

export default JuegosDashboard;
