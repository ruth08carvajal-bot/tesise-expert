import React, { useState, useEffect } from 'react';
import { obtenerResultadosDiagnostico } from '../../api/evaluacionService';

const ResultadosDiagnostico = ({ idNino, idEvaluacion }) => {
    const [diagnosticos, setDiagnosticos] = useState([]);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);

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

    if (cargando) return <div style={{textAlign: 'center', padding: '50px'}}>Procesando inferencia clínica...</div>;
    if (error) return <div style={{textAlign: 'center', padding: '50px', color: '#b71c1c'}}>{error}</div>;

    return (
        <div style={{ padding: '30px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
            <div style={{ borderBottom: '2px solid #2c3e50', marginBottom: '20px', paddingBottom: '10px' }}>
                <h2 style={{ color: '#2c3e50', margin: 0 }}>Reporte de Diagnóstico Experto</h2>
                <p style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>
                    Paciente ID: {idNino} | Evaluación ID: {idEvaluacion} | Fecha: {new Date().toLocaleDateString()}
                </p>
            </div>
            
            <div>
                {diagnosticos.filter((diag) => diag.fc_total > 0.5).length > 0 ? (
                    diagnosticos
                        .filter((diag) => diag.fc_total > 0.5)
                        .map((diag, index) => (
                            <div key={index} style={cardStyle}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <h3 style={{ margin: 0, color: '#1565c0' }}>{diag.nombre_diag}</h3>
                                    <span style={badgeStyle(diag.fc_total)}>
                                        CF: {(diag.fc_total * 100).toFixed(2)}%
                                    </span>
                                </div>
                            
                            <div style={{ marginTop: '15px' }}>
                                <p style={{ fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '5px' }}>
                                    Justificación Técnica (Trazas de Inferencia):
                                </p>
                                <ul style={{ fontSize: '0.85rem', color: '#555', paddingLeft: '20px' }}>
                                    {diag.explicacion.map((traza, i) => (
                                        <li key={i} style={{ marginBottom: '3px' }}>{traza}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ))
                ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
                        <p>No se encontraron evidencias suficientes para determinar un diagnóstico fonológico.</p>
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
                <button
                    onClick={() => window.open(`http://127.0.0.1:8003/evaluacion/generar-reporte-pdf/${idNino}/${idEvaluacion}`, '_blank')}
                    style={btnStyle}
                >
                    📄 Generar Reporte PDF
                </button>
            </div>
        </div>
    );
};

// Estilos de UI
const cardStyle = {
    backgroundColor: '#fff',
    borderLeft: '5px solid #1565c0',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
};

const badgeStyle = (fc) => ({
    backgroundColor: fc > 0.7 ? '#4caf50' : fc > 0.4 ? '#ff9800' : '#f44336',
    color: 'white',
    padding: '5px 12px',
    borderRadius: '20px',
    fontWeight: 'bold',
    fontSize: '0.8rem'
});

const btnStyle = {
    marginTop: '20px',
    padding: '10px 20px',
    backgroundColor: '#2c3e50',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontWeight: 'bold'
};

export default ResultadosDiagnostico;