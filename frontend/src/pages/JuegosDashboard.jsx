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
                                    <div style={styles.gamePreview}>
                                        {ejercicio.imagen ? (
                                            <img src={ejercicio.imagen} alt={ejercicio.nombre} style={styles.gameImage} />
                                        ) : (
                                            <div style={styles.gameImagePlaceholder}>
                                                <span style={styles.gameImageLabel}>J</span>
                                            </div>
                                        )}
                                        <div style={styles.gameInfo}>
                                            <h3 style={styles.gameTitle}>{ejercicio.nombre}</h3>
                                            <p style={styles.gameDescription}>{ejercicio.descripcion}</p>
                                            <div style={styles.gameMetaRow}>
                                                <span style={styles.gameMetaBadge}>{ejercicio.tipo_apoyo || 'Actividad'}</span>
                                                <span style={styles.gameMetaText}>{ejercicio.nivel || 'Nivel Básico'}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <button style={styles.enterButton} onClick={() => handleEntrarEjercicio(ejercicio)}>
                                        Jugar ahora
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
        gap: '18px',
        padding: '22px',
        borderTop: '1px solid #f0f0f0',
        transition: 'transform 0.24s ease, box-shadow 0.24s ease',
        cursor: 'pointer'
    },
    gameCardHover: {
        transform: 'translateY(-2px)',
        boxShadow: '0 20px 45px rgba(0,0,0,0.08)'
    },
    gamePreview: {
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        flex: 1
    },
    gameImage: {
        width: '100px',
        height: '100px',
        objectFit: 'cover',
        borderRadius: '18px',
        border: '2px solid #ecf0f1',
        backgroundColor: '#f8f9fa'
    },
    gameImagePlaceholder: {
        width: '100px',
        height: '100px',
        borderRadius: '18px',
        backgroundColor: '#dfe6ea',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '2px dashed #b2bec3'
    },
    gameImageLabel: {
        fontSize: '28px',
        color: '#636e72',
        fontWeight: '700'
    },
    gameInfo: {
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        minWidth: 0
    },
    gameTitle: {
        margin: 0,
        fontSize: '18px',
        color: '#2c3e50'
    },
    gameDescription: {
        margin: 0,
        color: '#7f8c8d',
        fontSize: '14px',
        lineHeight: '1.6'
    },
    gameMetaRow: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '10px',
        alignItems: 'center'
    },
    gameMetaBadge: {
        padding: '6px 12px',
        borderRadius: '999px',
        backgroundColor: '#ecf0f1',
        color: '#34495e',
        fontSize: '12px',
        fontWeight: '700'
    },
    gameMetaText: {
        color: '#95a5a6',
        fontSize: '12px'
    },
    enterButton: {
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '16px',
        padding: '14px 20px',
        cursor: 'pointer',
        boxShadow: '0 10px 25px rgba(0,0,0,0.08)'
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
