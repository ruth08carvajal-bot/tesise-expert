import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import axios from 'axios';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const API_URL = 'http://127.0.0.1:8003/evaluacion';

const GraficoProgreso = ({ idNino }) => {
    const [datosProgreso, setDatosProgreso] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const obtenerProgreso = async () => {
            try {
                // Obtener todas las evaluaciones del niño
                const response = await axios.get(`${API_URL}/historial-evaluaciones/${idNino}`);
                if (response.data.status === 'success') {
                    setDatosProgreso(response.data);
                }
            } catch (err) {
                console.error('Error obteniendo progreso:', err);
                setError('No se pudo cargar el gráfico de progreso');
            } finally {
                setCargando(false);
            }
        };

        if (idNino) {
            obtenerProgreso();
        }
    }, [idNino]);

    if (cargando) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.spinner}></div>
                <p>Cargando gráfico de progreso...</p>
            </div>
        );
    }

    if (error || !datosProgreso || datosProgreso.evaluaciones.length === 0) {
        return (
            <div style={styles.emptyContainer}>
                <p>📊 Aún no hay suficientes evaluaciones para mostrar el progreso.</p>
                <p style={styles.emptySubtext}>Completa al menos 2 evaluaciones para ver la evolución.</p>
            </div>
        );
    }

    // Preparar datos para el gráfico
    const labels = datosProgreso.evaluaciones.map(e => `${e.tipo}\n${e.fecha_formateada}`);
    
    // Calcular puntaje promedio por evaluación
    const puntajesPromedio = datosProgreso.evaluaciones.map(e => e.puntaje_promedio * 100);
    
    // Obtener mejores y peores fonemas
    const mejoresFonemas = datosProgreso.mejores_fonemas || [];
    const peoresFonemas = datosProgreso.peores_fonemas || [];

    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Puntaje promedio (%)',
                data: puntajesPromedio,
                borderColor: 'rgb(52, 152, 219)',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: 'rgb(52, 152, 219)',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
            }
        ]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Evolución del rendimiento',
                font: { size: 14 }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `Puntaje: ${context.parsed.y.toFixed(1)}%`;
                    }
                }
            }
        },
        scales: {
            y: {
                min: 0,
                max: 100,
                title: {
                    display: true,
                    text: 'Puntaje (%)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Evaluaciones'
                }
            }
        }
    };

    return (
        <div style={styles.container}>
            <h3 style={styles.title}>📈 Progreso del niño</h3>
            
            <div style={styles.chartContainer}>
                <Line data={data} options={options} />
            </div>

            {mejoresFonemas.length > 0 && (
                <div style={styles.mejoresSection}>
                    <h4 style={styles.subtitle}>✅ Fonemas con mejor rendimiento</h4>
                    <ul style={styles.lista}>
                        {mejoresFonemas.map((f, i) => (
                            <li key={i} style={styles.mejorItem}>
                                <strong>{f.descripcion}</strong>: {Math.round(f.promedio * 100)}% 
                                <span style={styles.tendenciaSube}>↑</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {peoresFonemas.length > 0 && (
                <div style={styles.peoresSection}>
                    <h4 style={styles.subtitle}>⚠️ Fonemas que requieren refuerzo</h4>
                    <ul style={styles.lista}>
                        {peoresFonemas.map((f, i) => (
                            <li key={i} style={styles.peorItem}>
                                <strong>{f.descripcion}</strong>: {Math.round(f.promedio * 100)}% 
                                <span style={styles.tendenciaBaja}>↓</span>
                                <span style={styles.recomendacion}> - Priorizar en práctica</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div style={styles.nota}>
                <p>💡 Los puntajes se calculan automáticamente según el rendimiento en las evaluaciones.</p>
            </div>
        </div>
    );
};

const styles = {
    container: {
        backgroundColor: 'white',
        borderRadius: '15px',
        padding: '20px',
        marginTop: '20px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
    },
    loadingContainer: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        color: '#555'
    },
    spinner: {
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        width: '30px',
        height: '30px',
        animation: 'spin 1s linear infinite',
        marginBottom: '10px'
    },
    emptyContainer: {
        textAlign: 'center',
        padding: '40px',
        backgroundColor: '#f8f9fa',
        borderRadius: '15px',
        color: '#7f8c8d'
    },
    emptySubtext: {
        fontSize: '12px',
        marginTop: '8px'
    },
    title: {
        margin: '0 0 15px 0',
        color: '#2c3e50',
        fontSize: '18px'
    },
    subtitle: {
        margin: '0 0 10px 0',
        fontSize: '14px'
    },
    chartContainer: {
        marginBottom: '25px'
    },
    mejoresSection: {
        marginBottom: '20px',
        padding: '15px',
        backgroundColor: '#d4edda',
        borderRadius: '10px'
    },
    peoresSection: {
        marginBottom: '20px',
        padding: '15px',
        backgroundColor: '#f8d7da',
        borderRadius: '10px'
    },
    lista: {
        margin: 0,
        paddingLeft: '20px'
    },
    mejorItem: {
        marginBottom: '5px',
        color: '#155724'
    },
    peorItem: {
        marginBottom: '5px',
        color: '#721c24'
    },
    tendenciaSube: {
        color: '#27ae60',
        fontWeight: 'bold',
        marginLeft: '8px'
    },
    tendenciaBaja: {
        color: '#e74c3c',
        fontWeight: 'bold',
        marginLeft: '8px'
    },
    recomendacion: {
        fontSize: '12px',
        color: '#856404',
        marginLeft: '8px'
    },
    nota: {
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#e8f4fd',
        borderRadius: '8px',
        fontSize: '12px',
        color: '#3498db'
    }
};

// Añadir keyframes
if (typeof document !== 'undefined') {
    const styleSheet = document.createElement("style");
    styleSheet.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(styleSheet);
}

export default GraficoProgreso;