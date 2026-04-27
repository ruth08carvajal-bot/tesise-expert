import React, { useState, useEffect } from 'react';
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
import { Line } from 'react-chartjs-2';

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
const NINO_API_URL = 'http://127.0.0.1:8003/ninos';

const ProgresoPage = ({ idNino, nombreNino, onBack }) => {
    const [datos, setDatos] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [nombre, setNombre] = useState(nombreNino || '');
    const [edad, setEdad] = useState(0);

    useEffect(() => {
        const cargarDatos = async () => {
            try {
                // Obtener datos del niño si no se pasó el nombre
                if (!nombreNino) {
                    try {
                        const ninoResponse = await axios.get(`${NINO_API_URL}/nino/${idNino}`);
                        if (ninoResponse.data) {
                            setNombre(ninoResponse.data.nombre);
                            setEdad(ninoResponse.data.edad);
                        }
                    } catch (err) {
                        console.error('Error obteniendo datos del niño:', err);
                    }
                }

                // Obtener historial de evaluaciones
                const response = await axios.get(`${API_URL}/historial-evaluaciones/${idNino}`);
                if (response.data.status === 'success') {
                    setDatos(response.data);
                }
            } catch (err) {
                console.error('Error cargando progreso:', err);
                setError('No se pudo cargar el progreso del niño');
            } finally {
                setCargando(false);
            }
        };

        if (idNino) {
            cargarDatos();
        }
    }, [idNino, nombreNino]);

    if (cargando) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.spinner}></div>
                <p>Cargando datos de progreso...</p>
            </div>
        );
    }

    if (error || !datos || datos.evaluaciones.length === 0) {
        return (
            <div style={styles.container}>
                <div style={styles.header}>
                    <button style={styles.backButton} onClick={onBack}>
                        ⬅ Volver al Dashboard
                    </button>
                </div>
                <div style={styles.errorCard}>
                    <p style={styles.errorText}>{error || 'No hay suficientes evaluaciones para mostrar el progreso'}</p>
                </div>
            </div>
        );
    }

    const { evaluaciones, mejores_fonemas, peores_fonemas } = datos;
    
    // Preparar datos para el gráfico
    const labels = evaluaciones.map(e => `${e.tipo_evaluacion}\n${e.fecha_formateada}`);
    const puntajes = evaluaciones.map(e => e.puntaje_promedio * 100);

    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Puntaje promedio (%)',
                data: puntajes,
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

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Evolución del rendimiento', font: { size: 16 } },
            tooltip: { callbacks: { label: (ctx) => `Puntaje: ${ctx.parsed.y.toFixed(1)}%` } }
        },
        scales: {
            y: { min: 0, max: 100, title: { display: true, text: 'Puntaje (%)' } },
            x: { title: { display: true, text: 'Evaluaciones' } }
        }
    };

    return (
        <div style={styles.container}>
            {/* Cabecera */}
            <div style={styles.header}>
                <button style={styles.backButton} onClick={onBack}>
                    ⬅ Volver al Dashboard
                </button>
                <h1 style={styles.title}>📈 Progreso de {nombre || `Niño ${idNino}`}</h1>
                {edad > 0 && (
                    <div style={styles.infoBadge}>
                        <span>{edad} años</span>
                    </div>
                )}
            </div>

            {/* Resumen */}
            <div style={styles.summaryCard}>
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{evaluaciones.length}</span>
                    <span style={styles.summaryLabel}>Evaluaciones</span>
                </div>
                <div style={styles.summaryDivider}></div>
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{mejores_fonemas.length}</span>
                    <span style={styles.summaryLabel}>✅ Fonemas correctos</span>
                </div>
                <div style={styles.summaryDivider}></div>
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{peores_fonemas.length}</span>
                    <span style={styles.summaryLabel}>🔴 Por mejorar</span>
                </div>
            </div>

            {/* Gráfico */}
            {evaluaciones.length >= 2 && (
                <div style={styles.chartCard}>
                    <h3 style={styles.sectionTitle}>📊 Evolución del rendimiento</h3>
                    <div style={styles.chartContainer}>
                        <Line data={chartData} options={chartOptions} />
                    </div>
                    <p style={styles.chartNote}>
                        💡 El puntaje promedio se calcula de todos los fonemas evaluados en cada sesión.
                    </p>
                </div>
            )}

            {/* Fonemas con mejor rendimiento */}
            {mejores_fonemas.length > 0 && (
                <div style={styles.successCard}>
                    <h3 style={styles.sectionTitle}>✅ Fonemas con mejor rendimiento ({mejores_fonemas.length})</h3>
                    <div style={styles.fonemasGrid}>
                        {mejores_fonemas.map((f, idx) => (
                            <div key={idx} style={styles.fonemaCardSuccess}>
                                <span style={styles.fonemaNombre}>{f.descripcion}</span>
                                <span style={styles.fonemaScore}>{Math.round(f.promedio * 100)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Fonemas que requieren refuerzo */}
            {peores_fonemas.length > 0 && (
                <div style={styles.dangerCard}>
                    <h3 style={styles.sectionTitle}>🔴 Fonemas que requieren refuerzo ({peores_fonemas.length})</h3>
                    <div style={styles.fonemasGrid}>
                        {peores_fonemas.map((f, idx) => (
                            <div key={idx} style={styles.fonemaCardDanger}>
                                <span style={styles.fonemaNombre}>{f.descripcion}</span>
                                <span style={styles.fonemaScore}>{Math.round(f.promedio * 100)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Historial de evaluaciones */}
            <div style={styles.historialCard}>
                <h3 style={styles.sectionTitle}>📅 Historial de evaluaciones</h3>
                <div style={styles.tableContainer}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Fecha</th>
                                <th>Tipo</th>
                                <th>Puntaje</th>
                            </tr>
                        </thead>
                        <tbody>
                            {evaluaciones.map((ev) => (
                                <tr key={ev.id_ev}>
                                    <td>#{ev.id_ev}</td>
                                    <td>{ev.fecha_formateada}</td>
                                    <td>{ev.tipo_evaluacion}</td>
                                    <td>
                                        <span style={{
                                            ...styles.puntajeBadge,
                                            backgroundColor: ev.puntaje_promedio >= 0.7 ? '#d4edda' : ev.puntaje_promedio >= 0.4 ? '#fff3cd' : '#f8d7da',
                                            color: ev.puntaje_promedio >= 0.7 ? '#155724' : ev.puntaje_promedio >= 0.4 ? '#856404' : '#721c24'
                                        }}>
                                            {Math.round(ev.puntaje_promedio * 100)}%
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Recomendaciones */}
            <div style={styles.recomendacionesCard}>
                <h3 style={styles.sectionTitle}>💡 Recomendaciones</h3>
                <ul style={styles.recomendacionesList}>
                    <li>Practicar los fonemas marcados como "requieren refuerzo" al menos 10 minutos al día.</li>
                    <li>Utilizar un espejo durante la práctica para que el niño vea cómo se mueve su boca.</li>
                    <li>Mantener sesiones cortas (10-15 minutos) pero constantes (3-4 veces por semana).</li>
                    <li>Celebrar los logros del niño, incluso los pequeños avances.</li>
                    <li>Programar la próxima evaluación en 3 meses para seguir el progreso.</li>
                </ul>
            </div>

            {/* Botón acciones */}
            <div style={styles.actions}>
                {evaluaciones.length > 0 && (
                    <button 
                        style={styles.pdfButton} 
                        onClick={() => window.open(`http://127.0.0.1:8003/evaluacion/generar-reporte-pdf/${idNino}/${evaluaciones[0]?.id_ev || ''}`, '_blank')}
                    >
                        📄 Generar Reporte PDF
                    </button>
                )}
                <button style={styles.backButtonFooter} onClick={onBack}>
                    ⬅ Volver al Dashboard
                </button>
            </div>
        </div>
    );
};

const styles = {
    container: {
        minHeight: '100vh',
        backgroundColor: '#f0f4f8',
        padding: '30px'
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
        borderTop: '4px solid #2c3e50',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite',
        marginBottom: '15px'
    },
    header: {
        marginBottom: '25px'
    },
    backButton: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '8px',
        cursor: 'pointer',
        marginBottom: '20px',
        fontSize: '14px'
    },
    title: {
        margin: '0 0 10px 0',
        fontSize: '28px',
        color: '#2c3e50'
    },
    infoBadge: {
        display: 'flex',
        gap: '10px',
        color: '#7f8c8d',
        fontSize: '14px'
    },
    summaryCard: {
        backgroundColor: 'white',
        borderRadius: '15px',
        padding: '20px',
        display: 'flex',
        justifyContent: 'space-around',
        marginBottom: '25px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
    },
    summaryItem: {
        textAlign: 'center'
    },
    summaryValue: {
        display: 'block',
        fontSize: '28px',
        fontWeight: 'bold',
        color: '#2c3e50'
    },
    summaryLabel: {
        fontSize: '12px',
        color: '#7f8c8d'
    },
    summaryDivider: {
        width: '1px',
        backgroundColor: '#e9ecef'
    },
    chartCard: {
        backgroundColor: 'white',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '25px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
    },
    sectionTitle: {
        margin: '0 0 15px 0',
        fontSize: '18px',
        color: '#2c3e50'
    },
    chartContainer: {
        height: '400px'
    },
    chartNote: {
        fontSize: '12px',
        color: '#7f8c8d',
        marginTop: '15px',
        textAlign: 'center'
    },
    successCard: {
        backgroundColor: '#d4edda',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '25px',
        borderLeft: '5px solid #28a745'
    },
    dangerCard: {
        backgroundColor: '#f8d7da',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '25px',
        borderLeft: '5px solid #dc3545'
    },
    fonemasGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '10px'
    },
    fonemaCardSuccess: {
        backgroundColor: 'white',
        padding: '10px 15px',
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderLeft: '3px solid #28a745'
    },
    fonemaCardDanger: {
        backgroundColor: 'white',
        padding: '10px 15px',
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderLeft: '3px solid #dc3545'
    },
    fonemaNombre: {
        fontSize: '14px',
        fontWeight: 'bold',
        color: '#2c3e50'
    },
    fonemaScore: {
        fontSize: '14px',
        fontWeight: 'bold',
        padding: '4px 10px',
        borderRadius: '20px',
        backgroundColor: '#f8f9fa'
    },
    historialCard: {
        backgroundColor: 'white',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '25px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
    },
    tableContainer: {
        overflowX: 'auto'
    },
    table: {
        width: '100%',
        borderCollapse: 'collapse'
    },
    puntajeBadge: {
        padding: '4px 10px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 'bold'
    },
    recomendacionesCard: {
        backgroundColor: '#e8f4fd',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '25px'
    },
    recomendacionesList: {
        margin: '0',
        paddingLeft: '20px',
        lineHeight: '1.8'
    },
    actions: {
        display: 'flex',
        gap: '15px',
        justifyContent: 'center',
        marginTop: '20px',
        flexWrap: 'wrap'
    },
    pdfButton: {
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        padding: '12px 25px',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    backButtonFooter: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '12px 25px',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    errorCard: {
        textAlign: 'center',
        padding: '50px',
        backgroundColor: 'white',
        borderRadius: '15px'
    },
    errorText: {
        color: '#e74c3c',
        marginBottom: '20px'
    }
};

// Añadir keyframes
const styleSheet = document.createElement("style");
styleSheet.textContent = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(styleSheet);

export default ProgresoPage;