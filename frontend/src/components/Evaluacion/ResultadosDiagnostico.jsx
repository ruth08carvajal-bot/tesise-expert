import React, { useState, useEffect } from 'react';
import { obtenerResultadosDiagnostico } from '../../api/evaluacionService';
import axios from 'axios';

const ResultadosDiagnostico = ({ idNino, idEvaluacion, onBack }) => {
    const [diagnosticos, setDiagnosticos] = useState([]);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [notas, setNotas] = useState('');
    const [guardandoNotas, setGuardandoNotas] = useState(false);
    
    useEffect(() => {
        const obtenerResultados = async () => {
            if (!idNino || !idEvaluacion) {
                setError('Falta información de evaluación para mostrar resultados.');
                setCargando(false);
                return;
            }

            try {
                const res = await obtenerResultadosDiagnostico(idNino, idEvaluacion);
                setDiagnosticos(res.diagnosticos || []);
            } catch (error) {
                console.error('Error al obtener diagnóstico', error);
                setError('No se pudo obtener el diagnóstico. Intenta de nuevo más tarde.');
            } finally {
                setCargando(false);
            }
        };

        obtenerResultados();
    }, [idNino, idEvaluacion]);

    const guardarNotas = async () => {
        if (!notas.trim()) return;
        
        setGuardandoNotas(true);
        try {
            const formData = new FormData();
            formData.append('id_evaluacion', idEvaluacion);
            formData.append('notas', notas);
            
            await axios.post('http://127.0.0.1:8003/evaluacion/agregar-notas', formData);
            alert('Notas guardadas correctamente');
        } catch (error) {
            console.error('Error guardando notas:', error);
            alert('Error al guardar las notas');
        } finally {
            setGuardandoNotas(false);
        }
    };

    if (cargando) {
        return (
            <div style={styles.container}>
                <div style={styles.videoBackground}>
                    <video autoPlay loop muted playsInline style={styles.video}>
                        <source src="/videos/fondo.mp4" type="video/mp4" />
                    </video>
                </div>
                <div style={styles.content}>
                    <div style={styles.loadingCard}>
                        <div style={styles.spinner}></div>
                        <p>Procesando inferencia clínica...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.container}>
                <div style={styles.videoBackground}>
                    <video autoPlay loop muted playsInline style={styles.video}>
                        <source src="/videos/fondo.mp4" type="video/mp4" />
                    </video>
                </div>
                <div style={styles.content}>
                    <div style={styles.errorCard}>
                        <p>{error}</p>
                        <button style={styles.backButton} onClick={onBack}>← Volver</button>
                    </div>
                </div>
            </div>
        );
    }

    const diagnosticosRelevantes = diagnosticos.filter((diag) => diag.fc_total > 0.5);

    return (
        <div style={styles.container}>
            {/* Video de fondo */}
            <div style={styles.videoBackground}>
                <video autoPlay loop muted playsInline style={styles.video}>
                    <source src="/videos/fondo.mp4" type="video/mp4" />
                </video>
            </div>

            {/* Contenido centrado */}
            <div style={styles.content}>
                <button style={styles.backButton} onClick={onBack}>← Volver</button>
                
                <div style={styles.card}>
                    <div style={styles.header}>
                        <h2 style={styles.title}>📋 Reporte de Diagnóstico Clínico</h2>
                        <p style={styles.subtitle}>
                            Evaluación ID: {idEvaluacion} | Fecha: {new Date().toLocaleDateString()}
                        </p>
                    </div>
                    
                    <div style={styles.diagnosticosSection}>
                        {diagnosticosRelevantes.length > 0 ? (
                            diagnosticosRelevantes.map((diag, index) => (
                                <div key={index} style={styles.diagnosticoCard}>
                                    <div style={styles.diagnosticoHeader}>
                                        <h3 style={styles.diagnosticoName}>{diag.nombre_diag}</h3>
                                        <span style={styles.badge(diag.fc_total)}>
                                            CF: {(diag.fc_total * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    
                                    <details style={styles.details}>
                                        <summary style={styles.summary}>📖 Ver justificación clínica</summary>
                                        <div style={styles.detailsContent}>
                                            {diag.explicacion && diag.explicacion.length > 0 ? (
                                                <ul style={styles.traceList}>
                                                    {diag.explicacion.map((traza, i) => (
                                                        <li key={i} style={styles.traceItem}>{traza}</li>
                                                    ))}
                                                </ul>
                                            ) : (
                                                <p>No hay trazabilidad disponible.</p>
                                            )}
                                        </div>
                                    </details>
                                </div>
                            ))
                        ) : (
                            <div style={styles.emptyState}>
                                <p>✅ No se encontraron diagnósticos con certeza suficiente.</p>
                                <p style={styles.emptyStateSub}>Esto indica que el desarrollo está dentro de lo esperado.</p>
                            </div>
                        )}
                    </div>

                    {/* Sección de notas */}
                    <div style={styles.notasSection}>
                        <h3 style={styles.sectionTitle}>📝 Notas del Tutor</h3>
                        <textarea
                            style={styles.textarea}
                            placeholder="Agregue observaciones adicionales, comentarios sobre el comportamiento del niño durante la evaluación..."
                            value={notas}
                            onChange={(e) => setNotas(e.target.value)}
                            rows={3}
                        />
                        <button 
                            onClick={guardarNotas} 
                            style={styles.saveButton}
                            disabled={guardandoNotas || !notas.trim()}
                        >
                            {guardandoNotas ? 'Guardando...' : 'Guardar Notas'}
                        </button>
                    </div>

                    <div style={styles.actions}>
                        <button
                            onClick={() => window.open(`http://127.0.0.1:8003/evaluacion/generar-reporte-pdf/${idNino}/${idEvaluacion}`, '_blank')}
                            style={styles.pdfButton}
                        >
                            📄 Generar Reporte PDF
                        </button>
                        <button style={styles.closeButton} onClick={onBack}>
                            Cerrar
                        </button>
                    </div>
                </div>
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
    videoBackground: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 0
    },
    video: {
        width: '100%',
        height: '100%',
        objectFit: 'cover'
    },
    content: {
        position: 'relative',
        zIndex: 1,
        minHeight: '100vh',
        padding: '30px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
    },
    backButton: {
        position: 'fixed',
        top: '20px',
        left: '20px',
        backgroundColor: 'rgba(108, 117, 125, 0.9)',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '30px',
        cursor: 'pointer',
        fontSize: '14px',
        backdropFilter: 'blur(5px)',
        zIndex: 10
    },
    card: {
        maxWidth: '800px',
        width: '90%',
        margin: '60px auto',
        backgroundColor: 'rgba(255, 255, 255, 0.92)',
        borderRadius: '20px',
        padding: '30px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
        backdropFilter: 'blur(5px)'
    },
    loadingCard: {
        maxWidth: '400px',
        width: '90%',
        margin: 'auto',
        backgroundColor: 'rgba(255, 255, 255, 0.92)',
        borderRadius: '20px',
        padding: '40px',
        textAlign: 'center',
        backdropFilter: 'blur(5px)'
    },
    errorCard: {
        maxWidth: '400px',
        width: '90%',
        margin: 'auto',
        backgroundColor: 'rgba(255, 255, 255, 0.92)',
        borderRadius: '20px',
        padding: '40px',
        textAlign: 'center',
        backdropFilter: 'blur(5px)'
    },
    spinner: {
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #2c3e50',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite',
        margin: '0 auto 15px'
    },
    header: {
        borderBottom: '2px solid #2c3e50',
        marginBottom: '25px',
        paddingBottom: '15px'
    },
    title: {
        margin: 0,
        fontSize: '24px',
        color: '#2c3e50'
    },
    subtitle: {
        margin: '8px 0 0',
        fontSize: '13px',
        color: '#7f8c8d'
    },
    diagnosticosSection: {
        marginBottom: '25px'
    },
    diagnosticoCard: {
        backgroundColor: 'white',
        borderLeft: '5px solid #3498db',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    },
    diagnosticoHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '15px',
        flexWrap: 'wrap',
        gap: '10px'
    },
    diagnosticoName: {
        margin: 0,
        fontSize: '17px',
        color: '#2c3e50'
    },
    badge: (fc) => ({
        backgroundColor: fc > 0.7 ? '#27ae60' : '#f39c12',
        color: 'white',
        padding: '4px 12px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 'bold'
    }),
    details: {
        marginTop: '10px'
    },
    summary: {
        cursor: 'pointer',
        color: '#3498db',
        fontSize: '13px',
        fontWeight: '500'
    },
    detailsContent: {
        marginTop: '12px',
        padding: '15px',
        backgroundColor: '#f8f9fa',
        borderRadius: '10px',
        fontSize: '13px'
    },
    traceList: {
        margin: 0,
        paddingLeft: '20px'
    },
    traceItem: {
        marginBottom: '8px',
        color: '#555'
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#27ae60'
    },
    emptyStateSub: {
        fontSize: '13px',
        color: '#7f8c8d',
        marginTop: '8px'
    },
    notasSection: {
        backgroundColor: '#f8f9fa',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '25px',
        border: '1px solid #e9ecef'
    },
    sectionTitle: {
        margin: '0 0 15px 0',
        fontSize: '16px',
        color: '#2c3e50'
    },
    textarea: {
        width: '100%',
        padding: '12px',
        borderRadius: '8px',
        border: '1px solid #ddd',
        fontSize: '14px',
        fontFamily: 'inherit',
        resize: 'vertical',
        marginBottom: '10px',
        boxSizing: 'border-box'
    },
    saveButton: {
        padding: '8px 20px',
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px'
    },
    actions: {
        display: 'flex',
        gap: '15px',
        justifyContent: 'center',
        marginTop: '10px'
    },
    pdfButton: {
        padding: '12px 24px',
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '30px',
        cursor: 'pointer',
        fontWeight: '500'
    },
    closeButton: {
        padding: '12px 24px',
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        borderRadius: '30px',
        cursor: 'pointer'
    }
};

// Añadir keyframes
const styleSheet = document.createElement("style");
styleSheet.textContent = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(styleSheet);

export default ResultadosDiagnostico;