import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PracticaEjercicio from '../components/Ejercicio/PracticaEjercicio';

const API_URL = 'http://127.0.0.1:8003/ejercicios';

const NinoDashboard = ({ usuario, onLogout }) => {
    const [ejercicios, setEjercicios] = useState([]);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [ejercicioSeleccionado, setEjercicioSeleccionado] = useState(null);
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });

    useEffect(() => {
        const cargarEjercicios = async () => {
            try {
                const response = await axios.get(`${API_URL}/mis-ejercicios/${usuario.id_nino}`);
                if (response.data.status === 'success') {
                    setEjercicios(response.data.ejercicios);
                }
            } catch (err) {
                console.error('Error cargando ejercicios:', err);
                setError('No se pudieron cargar tus ejercicios. Intenta más tarde.');
            } finally {
                setCargando(false);
            }
        };

        if (usuario.id_nino) {
            cargarEjercicios();
        }
    }, [usuario.id_nino]);

    const handlePracticar = (ejercicio) => {
        setEjercicioSeleccionado(ejercicio);
    };

    const handleVolver = () => {
        setEjercicioSeleccionado(null);
        window.location.reload();
    };

    const handleGuardarProgreso = async (idEjercicio, puntaje, tiempo) => {
        try {
            const response = await axios.post(`${API_URL}/guardar-progreso`, {
                id_nino: usuario.id_nino,
                id_ejercicio: idEjercicio,
                puntaje_obtenido: puntaje,
                tiempo_empleado: tiempo
            });
            
            if (response.data.status === 'success') {
                setMensaje({ 
                    texto: `¡Excelente! Puntaje: ${Math.round(puntaje * 100)}%`, 
                    tipo: 'success' 
                });
                setTimeout(() => setMensaje({ texto: '', tipo: '' }), 3000);
            }
        } catch (err) {
            console.error('Error guardando progreso:', err);
            setMensaje({ texto: 'Error al guardar tu progreso', tipo: 'error' });
        }
    };

    if (cargando) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.spinner}></div>
                <p>Cargando tus ejercicios...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.container}>
                <p style={styles.errorText}>{error}</p>
                <button onClick={onLogout} style={styles.logoutButton}>Salir</button>
            </div>
        );
    }

    if (ejercicioSeleccionado) {
        return (
            <PracticaEjercicio 
                ejercicio={ejercicioSeleccionado}
                idNino={usuario.id_nino}
                onGuardarProgreso={handleGuardarProgreso}
                onVolver={handleVolver}
            />
        );
    }

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <div>
                    <h2 style={styles.title}>🎮 ¡Hola, {usuario.nombre}!</h2>
                    <p style={styles.subtitle}>Practica estos ejercicios para mejorar tu pronunciación</p>
                </div>
                <button onClick={onLogout} style={styles.logoutButton}>Cerrar Sesión</button>
            </header>

            {mensaje.texto && (
                <div style={{
                    ...styles.mensaje,
                    backgroundColor: mensaje.tipo === 'success' ? '#d4edda' : '#f8d7da',
                    color: mensaje.tipo === 'success' ? '#155724' : '#721c24'
                }}>
                    {mensaje.texto}
                </div>
            )}

            <div style={styles.ejerciciosGrid}>
                {ejercicios.length === 0 ? (
                    <div style={styles.emptyState}>
                        <p>🎉 No tienes ejercicios pendientes por ahora.</p>
                        <p>¡Sigue practicando, vas muy bien!</p>
                    </div>
                ) : (
                    ejercicios.map((ej) => (
                        <div key={ej.id_ejercicio} style={styles.ejercicioCard}>
                            <div style={styles.nivelBadge(ej.nivel)}>
                                {ej.nivel === 'Bajo' ? '🟢 Fácil' : ej.nivel === 'Medio' ? '🟡 Medio' : '🔴 Avanzado'}
                            </div>
                            <h3 style={styles.ejercicioNombre}>{ej.nombre}</h3>
                            <p style={styles.ejercicioDescripcion}>{ej.descripcion}</p>
                            {ej.rendimiento_previo > 0 && (
                                <p style={styles.rendimiento}>
                                    📊 Tu mejor puntaje: {Math.round(ej.rendimiento_previo * 100)}%
                                </p>
                            )}
                            <button 
                                style={styles.practicarButton}
                                onClick={() => handlePracticar(ej)}
                            >
                                🎤 Practicar
                            </button>
                        </div>
                    ))
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
    loadingContainer: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        color: '#555'
    },
    spinner: {
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'white',
        padding: '20px 30px',
        borderRadius: '15px',
        marginBottom: '30px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
    },
    title: {
        margin: 0,
        color: '#2c3e50',
        fontSize: '24px'
    },
    subtitle: {
        margin: '5px 0 0',
        color: '#7f8c8d',
        fontSize: '14px'
    },
    logoutButton: {
        padding: '10px 20px',
        backgroundColor: '#e74c3c',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    mensaje: {
        padding: '12px 20px',
        borderRadius: '10px',
        marginBottom: '20px',
        textAlign: 'center'
    },
    ejerciciosGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '20px'
    },
    ejercicioCard: {
        backgroundColor: 'white',
        borderRadius: '15px',
        padding: '20px',
        position: 'relative',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        transition: 'transform 0.2s'
    },
    nivelBadge: (nivel) => ({
        position: 'absolute',
        top: '15px',
        right: '15px',
        fontSize: '12px',
        fontWeight: 'bold',
        padding: '5px 10px',
        borderRadius: '20px',
        backgroundColor: nivel === 'Bajo' ? '#d4edda' : nivel === 'Medio' ? '#fff3cd' : '#f8d7da',
        color: nivel === 'Bajo' ? '#155724' : nivel === 'Medio' ? '#856404' : '#721c24'
    }),
    ejercicioNombre: {
        margin: '0 0 10px 0',
        fontSize: '18px',
        color: '#2c3e50',
        paddingRight: '60px'
    },
    ejercicioDescripcion: {
        fontSize: '14px',
        color: '#555',
        lineHeight: '1.5',
        marginBottom: '15px'
    },
    rendimiento: {
        fontSize: '12px',
        color: '#3498db',
        marginBottom: '15px'
    },
    practicarButton: {
        width: '100%',
        padding: '12px',
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: 'bold',
        fontSize: '16px'
    },
    emptyState: {
        textAlign: 'center',
        padding: '60px',
        backgroundColor: 'white',
        borderRadius: '15px',
        color: '#27ae60'
    },
    errorText: {
        color: '#e74c3c',
        textAlign: 'center',
        marginBottom: '20px'
    }
};

// Añadir keyframes para el spinner
const styleSheet = document.createElement("style");
styleSheet.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(styleSheet);

export default NinoDashboard;