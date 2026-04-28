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
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.loadingContainer}>
                    <div style={styles.spinner}></div>
                    <p>Cargando datos de progreso...</p>
                </div>
            </div>
        );
    }

    if (error || !datos || datos.evaluaciones.length === 0) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.content}>
                    <button style={styles.backButton} onClick={onBack}>← Volver</button>
                    <div style={styles.errorCard}>
                        <p>{error || 'No hay suficientes evaluaciones para mostrar el progreso'}</p>
                    </div>
                </div>
            </div>
        );
    }

    const { evaluaciones, mejores_fonemas, peores_fonemas } = datos;
    
    const labels = evaluaciones.map(e => `${e.tipo_evaluacion}\n${e.fecha_formateada}`);
    const puntajes = evaluaciones.map(e => e.puntaje_promedio * 100);

    const chartData = {
        labels: labels,
        datasets: [{
            label: 'Puntaje promedio (%)',
            data: puntajes,
            borderColor: '#3498db',
            backgroundColor: 'rgba(52, 152, 219, 0.1)',
            tension: 0.3,
            fill: true,
            pointRadius: 5,
            pointBackgroundColor: '#3498db',
            pointBorderColor: 'white',
            pointBorderWidth: 2
        }]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Evolución del rendimiento', font: { size: 14 } }
        },
        scales: {
            y: { min: 0, max: 100, title: { display: true, text: 'Puntaje (%)' } },
            x: { title: { display: true, text: 'Evaluaciones' } }
        }
    };

    return (
        <div style={styles.container}>
            {/* Fondo de imagen */}
            <div style={styles.backgroundImage} />
            
            {/* Contenido */}
            <div style={styles.content}>
                <button style={styles.backButton} onClick={onBack}>← Volver</button>
                
                <div style={styles.header}>
                    <h1 style={styles.title}>📈 Progreso de {nombre || `Niño ${idNino}`}</h1>
                    {edad > 0 && <span style={styles.ageBadge}>{edad} años</span>}
                </div>

                {/* Tarjetas resumen */}
                <div style={styles.summaryCards}>
                    <div style={styles.summaryCard}>
                        <div style={styles.summaryValue}>{evaluaciones.length}</div>
                        <div style={styles.summaryLabel}>Evaluaciones</div>
                    </div>
                    <div style={styles.summaryCard}>
                        <div style={styles.summaryValue}>{mejores_fonemas.length}</div>
                        <div style={styles.summaryLabel}>✅ Correctos</div>
                    </div>
                    <div style={styles.summaryCard}>
                        <div style={styles.summaryValue}>{peores_fonemas.length}</div>
                        <div style={styles.summaryLabel}>🔴 Por mejorar</div>
                    </div>
                </div>

                {/* Gráfico */}
                {evaluaciones.length >= 2 && (
                    <div style={styles.chartCard}>
                        <div style={styles.chartContainer}>
                            <Line data={chartData} options={chartOptions} />
                        </div>
                    </div>
                )}

                {/* Dos columnas: Mejores y Peores fonemas */}
                <div style={styles.twoColumns}>
                    {mejores_fonemas.length > 0 && (
                        <div style={styles.successCard}>
                            <h3>✅ Mejor rendimiento</h3>
                            {mejores_fonemas.slice(0, 5).map((f, idx) => (
                                <div key={idx} style={styles.fonemaRow}>
                                    <span>{f.descripcion}</span>
                                    <span style={styles.scoreGood}>{Math.round(f.promedio * 100)}%</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {peores_fonemas.length > 0 && (
                        <div style={styles.dangerCard}>
                            <h3>🔴 Requieren refuerzo</h3>
                            {peores_fonemas.slice(0, 5).map((f, idx) => (
                                <div key={idx} style={styles.fonemaRow}>
                                    <span>{f.descripcion}</span>
                                    <span style={styles.scoreBad}>{Math.round(f.promedio * 100)}%</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Historial de evaluaciones (compacto) */}
                <div style={styles.historialCard}>
                    <h3>📅 Historial</h3>
                    <div style={styles.historialList}>
                        {evaluaciones.map((ev) => (
                            <div key={ev.id_ev} style={styles.historialItem}>
                                <span>{ev.fecha_formateada}</span>
                                <span>{ev.tipo_evaluacion}</span>
                                <span style={{
                                    ...styles.puntajeBadge,
                                    backgroundColor: ev.puntaje_promedio >= 0.7 ? '#27ae60' : ev.puntaje_promedio >= 0.4 ? '#f39c12' : '#e74c3c',
                                    color: '#ffffff'
                                }}>
                                    {Math.round(ev.puntaje_promedio * 100)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recomendaciones compactas */}
                <div style={styles.recomendacionesCard}>
                    <h3>💡 Recomendaciones</h3>
                    <ul style={styles.recomendacionesList}>
                        <li>Practicar los fonemas marcados como "requieren refuerzo" al menos 10 minutos al día.</li>
                        <li>Utilizar un espejo durante la práctica.</li>
                        <li>Mantener sesiones cortas (10-15 minutos) pero constantes.</li>
                        <li>Programar la próxima evaluación en 3 meses.</li>
                    </ul>
                </div>

                {/* Botones */}
                <div style={styles.actions}>
                    {evaluaciones.length > 0 && (
                        <button style={styles.pdfButton} onClick={() => window.open(`http://127.0.0.1:8003/evaluacion/generar-reporte-pdf/${idNino}/${evaluaciones[0]?.id_ev || ''}`, '_blank')}>
                            📄 Generar PDF
                        </button>
                    )}
                    <button style={styles.closeButton} onClick={onBack}>Cerrar</button>
                </div>
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
        backgroundImage: 'url("/images/fondo_progreso.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        zIndex: 0
    },
    content: {
        position: 'relative',
        zIndex: 1,
        maxWidth: '900px',
        margin: '0 auto',
        padding: '20px',
        backgroundColor: 'rgba(111, 155, 142, 0.44)',
        borderRadius: '20px',
        minHeight: '100vh'
    },
    backButton: {
        backgroundColor: '#7d706c',
        color: '#ffffff',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '20px',
        cursor: 'pointer',
        marginBottom: '20px',
        fontSize: '13px'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '10px'
    },
    title: {
        fontSize: '24px',
        color: '#2c3e50',
        margin: 0
    },
    ageBadge: {
        backgroundColor: '#3498db',
        color: 'white',
        padding: '5px 12px',
        borderRadius: '20px',
        fontSize: '13px'
    },
    summaryCards: {
        display: 'flex',
        gap: '15px',
        marginBottom: '20px',
        flexWrap: 'wrap'
    },
    summaryCard: {
        flex: 1,
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        padding: '15px',
        textAlign: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        minWidth: '100px'
    },
    summaryValue: {
        fontSize: '28px',
        fontWeight: 'bold',
        color: '#2c3e50'
    },
    summaryLabel: {
        fontSize: '12px',
        color: '#7f8c8d'
    },
    chartCard: {
        backgroundColor: '#ffffffeb',
        borderRadius: '12px',
        padding: '15px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    },
    chartContainer: {
        height: '280px'
    },
    twoColumns: {
        display: 'flex',
        gap: '20px',
        marginBottom: '20px',
        flexWrap: 'wrap'
    },
    successCard: {
        flex: 1,
        backgroundColor: '#d4eddaa7',
        borderRadius: '12px',
        padding: '15px',
        borderLeft: '4px solid #27ae60'
    },
    dangerCard: {
        flex: 1,
        backgroundColor: '#f8d7dac5',
        borderRadius: '12px',
        padding: '15px',
        borderLeft: '4px solid #e74c3c'
    },
    fonemaRow: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 0',
        borderBottom: '1px solid rgba(0,0,0,0.05)'
    },
    scoreGood: {
        backgroundColor: '#27ae60',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '12px',
        fontSize: '12px'
    },
    scoreBad: {
        backgroundColor: '#e74c3c',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '12px',
        fontSize: '12px'
    },
    historialCard: {
        backgroundColor: '#a5bdc98d',
        borderRadius: '12px',
        padding: '15px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    },
    historialList: {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
    },
    historialItem: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px',
        backgroundColor: '#fcfffe75',
        borderRadius: '8px'
    },
    puntajeBadge: {
        padding: '4px 10px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 'bold'
    },
    recomendacionesCard: {
        backgroundColor: '#e8f4fd',
        borderRadius: '12px',
        padding: '15px',
        marginBottom: '20px'
    },
    recomendacionesList: {
        margin: '0',
        paddingLeft: '20px',
        lineHeight: '1.6',
        fontSize: '13px'
    },
    actions: {
        display: 'flex',
        gap: '15px',
        justifyContent: 'center',
        marginTop: '10px',
        marginBottom: '20px'
    },
    pdfButton: {
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '25px',
        cursor: 'pointer'
    },
    closeButton: {
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '25px',
        cursor: 'pointer'
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
    errorCard: {
        textAlign: 'center',
        padding: '40px',
        backgroundColor: 'white',
        borderRadius: '12px'
    }
};

// Añadir keyframes
const styleSheet = document.createElement("style");
styleSheet.textContent = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(styleSheet);

export default ProgresoPage;