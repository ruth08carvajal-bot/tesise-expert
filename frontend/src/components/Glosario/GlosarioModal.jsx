import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8003/glosario';

const GlosarioModal = ({ onClose }) => {
    const [terminos, setTerminos] = useState([]);
    const [terminoSeleccionado, setTerminoSeleccionado] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [busqueda, setBusqueda] = useState('');
    const [categoriaSeleccionada, setCategoriaSeleccionada] = useState('');
    const [categorias, setCategorias] = useState([]);

    useEffect(() => {
        cargarCategorias();
        cargarTerminos();
    }, []);

    const cargarCategorias = async () => {
        try {
            const response = await axios.get(`${API_URL}/categorias`);
            if (response.data.status === 'success') {
                setCategorias(response.data.categorias);
            }
        } catch (error) {
            console.error('Error cargando categorías:', error);
        }
    };

    const cargarTerminos = async () => {
        setCargando(true);
        try {
            let url = `${API_URL}/buscar`;
            const params = new URLSearchParams();
            
            if (busqueda) {
                params.append('q', busqueda);
            }
            if (categoriaSeleccionada) {
                params.append('categoria', categoriaSeleccionada);
            }
            
            if (params.toString()) {
                url += `?${params.toString()}`;
            }
            
            const response = await axios.get(url);
            if (response.data.status === 'success') {
                setTerminos(response.data.terminos);
            }
        } catch (error) {
            console.error('Error cargando términos:', error);
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            cargarTerminos();
        }, 300);
        
        return () => clearTimeout(timer);
    }, [busqueda, categoriaSeleccionada]);

    const getCategoriaColor = (categoria) => {
        const colores = {
            'Habla': '#4caf50',
            'Lenguaje': '#2196f3',
            'Lectura': '#ff9800',
            'Escritura': '#9c27b0',
            'Percepción': '#00bcd4',
            'Fluidez': '#e91e63',
            'Mixto': '#ff5722',
            'Procesamiento': '#009688',
            'Voz': '#f44336',
            'Tecnología': '#607d8b',
            'Errores del habla': '#ffc107',
            'Conceptos clave': '#3f51b5',
            'Materiales': '#8bc34a'
        };
        return colores[categoria] || '#757575';
    };

    return (
        <div style={styles.modalOverlay} onClick={onClose}>
            <div style={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
                {/* Cabecera */}
                <div style={styles.header}>
                    <h3 style={styles.title}>📖 Glosario de Términos</h3>
                    <button style={styles.closeButton} onClick={onClose}>✕</button>
                </div>

                {/* Búsqueda y filtros */}
                <div style={styles.filtrosContainer}>
                    <input
                        type="text"
                        style={styles.busquedaInput}
                        placeholder="🔍 Buscar término..."
                        value={busqueda}
                        onChange={(e) => setBusqueda(e.target.value)}
                    />
                    
                    <select
                        style={styles.categoriaSelect}
                        value={categoriaSeleccionada}
                        onChange={(e) => setCategoriaSeleccionada(e.target.value)}
                    >
                        <option value="">Todas las categorías</option>
                        {categorias.map((cat, idx) => (
                            <option key={idx} value={cat.categoria}>
                                {cat.categoria} ({cat.cantidad})
                            </option>
                        ))}
                    </select>
                </div>

                {/* Lista de términos */}
                <div style={styles.listaContainer}>
                    {cargando ? (
                        <div style={styles.loadingContainer}>
                            <div style={styles.spinner}></div>
                            <p>Cargando glosario...</p>
                        </div>
                    ) : terminos.length === 0 ? (
                        <div style={styles.vacioContainer}>
                            <p>📭 No se encontraron términos</p>
                            <p style={styles.vacioSubtexto}>Intenta con otra búsqueda</p>
                        </div>
                    ) : (
                        terminos.map((term) => (
                            <div
                                key={term.id_glosario}
                                style={styles.terminoCard}
                                onClick={() => setTerminoSeleccionado(
                                    terminoSeleccionado?.id_glosario === term.id_glosario ? null : term
                                )}
                            >
                                <div style={styles.terminoHeader}>
                                    <div style={styles.terminoTitulos}>
                                        <span style={styles.terminoTecnico}>{term.termino_tecnico}</span>
                                        <span style={styles.terminoAmigable}>→ {term.termino_amigable}</span>
                                    </div>
                                    <span style={{
                                        ...styles.categoriaBadge,
                                        backgroundColor: getCategoriaColor(term.categoria)
                                    }}>
                                        {term.categoria}
                                    </span>
                                </div>
                                
                                <p style={styles.definicionSimple}>{term.definicion_simple}</p>
                                
                                {terminoSeleccionado?.id_glosario === term.id_glosario && (
                                    <div style={styles.explicacionDetallada}>
                                        <div style={styles.explicacionHeader}>
                                            <span>📚 Explicación detallada</span>
                                        </div>
                                        <p>{term.explicacion_detallada}</p>
                                        {term.id_diag && (
                                            <div style={styles.relacionDiagnostico}>
                                                🔗 Relacionado con: <strong>Diagnóstico clínico</strong>
                                            </div>
                                        )}
                                    </div>
                                )}
                                
                                <div style={styles.verMas}>
                                    {terminoSeleccionado?.id_glosario === term.id_glosario ? '▲ Ver menos' : '▼ Ver más'}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer */}
                <div style={styles.footer}>
                    <p style={styles.footerTexto}>
                        📌 {terminos.length} términos encontrados
                    </p>
                    <button style={styles.cerrarButton} onClick={onClose}>
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    );
};

const styles = {
    modalOverlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1100
    },
    modalContainer: {
        backgroundColor: 'white',
        borderRadius: '16px',
        width: '90%',
        maxWidth: '800px',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
        overflow: 'hidden'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 20px',
        backgroundColor: '#2c3e50',
        color: 'white'
    },
    title: {
        margin: 0,
        fontSize: '18px'
    },
    closeButton: {
        background: 'none',
        border: 'none',
        color: 'white',
        fontSize: '22px',
        cursor: 'pointer',
        padding: '0 5px'
    },
    filtrosContainer: {
        padding: '16px 20px',
        backgroundColor: '#f8f9fa',
        borderBottom: '1px solid #e9ecef',
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap'
    },
    busquedaInput: {
        flex: 2,
        padding: '10px 14px',
        border: '1px solid #ddd',
        borderRadius: '25px',
        fontSize: '14px',
        outline: 'none'
    },
    categoriaSelect: {
        flex: 1,
        padding: '10px 14px',
        border: '1px solid #ddd',
        borderRadius: '25px',
        fontSize: '14px',
        backgroundColor: 'white',
        cursor: 'pointer'
    },
    listaContainer: {
        flex: 1,
        overflowY: 'auto',
        padding: '16px 20px',
        backgroundColor: '#f5f7fa'
    },
    loadingContainer: {
        textAlign: 'center',
        padding: '40px',
        color: '#555'
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
    vacioContainer: {
        textAlign: 'center',
        padding: '40px',
        color: '#888'
    },
    vacioSubtexto: {
        fontSize: '12px',
        marginTop: '8px'
    },
    terminoCard: {
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        cursor: 'pointer',
        transition: 'all 0.2s'
    },
    terminoHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '10px',
        marginBottom: '10px'
    },
    terminoTitulos: {
        flex: 1
    },
    terminoTecnico: {
        fontWeight: 'bold',
        fontSize: '16px',
        color: '#2c3e50',
        marginRight: '8px'
    },
    terminoAmigable: {
        fontSize: '13px',
        color: '#3498db'
    },
    categoriaBadge: {
        padding: '4px 10px',
        borderRadius: '20px',
        fontSize: '11px',
        fontWeight: 'bold',
        color: 'white'
    },
    definicionSimple: {
        fontSize: '14px',
        color: '#555',
        marginBottom: '10px',
        lineHeight: '1.4'
    },
    explicacionDetallada: {
        marginTop: '12px',
        padding: '12px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        borderLeft: '3px solid #2c3e50'
    },
    explicacionHeader: {
        fontSize: '13px',
        fontWeight: 'bold',
        color: '#2c3e50',
        marginBottom: '8px'
    },
    relacionDiagnostico: {
        marginTop: '10px',
        paddingTop: '8px',
        fontSize: '12px',
        color: '#6c757d',
        borderTop: '1px solid #dee2e6'
    },
    verMas: {
        fontSize: '11px',
        color: '#3498db',
        marginTop: '8px',
        textAlign: 'right'
    },
    footer: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '12px 20px',
        borderTop: '1px solid #e9ecef',
        backgroundColor: 'white'
    },
    footerTexto: {
        margin: 0,
        fontSize: '12px',
        color: '#6c757d'
    },
    cerrarButton: {
        padding: '8px 20px',
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '20px',
        cursor: 'pointer',
        fontSize: '13px'
    }
};

// Añadir keyframes para el spinner
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

export default GlosarioModal;