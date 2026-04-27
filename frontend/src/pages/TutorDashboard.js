import React, { useState, useEffect, useCallback } from 'react';
import { registrarNino, obtenerNinos } from '../api/ninosService';
import AnamnesisForm from './AnamnesisForm';
import EvaluacionFonetica from '../components/Evaluacion/EvaluacionFonetica';
import ResultadosDiagnostico from '../components/Evaluacion/ResultadosDiagnostico';
import { iniciarEvaluacion } from '../api/evaluacionService';
import ModuloExplicativo from '../components/Explicacion/ModuloExplicativo';

const TutorDashboard = ({ usuario, onLogout, onVerProgreso }) => {
    const [ninos, setNinos] = useState([]);
    const [nuevoNino, setNuevoNino] = useState({
        nombre: '', f_nac: '', genero: 'M', escolaridad: 'Inicial', parentesco: 'Padre/Madre'
    });
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [showAnamnesis, setShowAnamnesis] = useState(false);
    const [selectedNino, setSelectedNino] = useState(null);

    // Estados para evaluación
    const [showEvaluacion, setShowEvaluacion] = useState(false);
    const [showResultados, setShowResultados] = useState(false);
    const [idEvaluacionActual, setIdEvaluacionActual] = useState(null);
    
    // Estados para selector de evaluaciones
    const [mostrarSelectorEvaluacion, setMostrarSelectorEvaluacion] = useState(false);
    const [evaluacionesDisponibles, setEvaluacionesDisponibles] = useState([]);
    
    // Estado para explicación de resultados
    const [showExplicacion, setShowExplicacion] = useState(false);
    const [ninoParaExplicacion, setNinoParaExplicacion] = useState(null);

    const cargarNinos = useCallback(async () => {
        if (!usuario || !usuario.id_tut) {
            return;
        }

        try {
            const data = await obtenerNinos(usuario.id_tut);
            setNinos(data);
        } catch (err) {
            console.error("Error al cargar niños", err);
            setMensaje({ texto: "Error al cargar la lista de niños", tipo: 'error' });
        }
    }, [usuario]);

    useEffect(() => {
        cargarNinos();
    }, [cargarNinos]);

    const handleRegister = async (e) => {
        e.preventDefault();
        
        // VALIDACIÓN DE EDAD (mínimo 5 años)
        const fechaNacimiento = new Date(nuevoNino.f_nac);
        const hoy = new Date();
        let edad = hoy.getFullYear() - fechaNacimiento.getFullYear();
        const mesDiff = hoy.getMonth() - fechaNacimiento.getMonth();
        
        if (mesDiff < 0 || (mesDiff === 0 && hoy.getDate() < fechaNacimiento.getDate())) {
            edad--;
        }
        
        if (edad < 5) {
            setMensaje({ 
                texto: `El niño debe tener al menos 5 años para ser evaluado. Edad actual: ${edad} años.`, 
                tipo: 'error' 
            });
            setTimeout(() => setMensaje({ texto: '', tipo: '' }), 4000);
            return;
        }
        
        // Si pasa la validación, registrar
        try {
            await registrarNino({ ...nuevoNino, id_tut: usuario.id_tut });
            setNuevoNino({ nombre: '', f_nac: '', genero: 'M', escolaridad: 'Inicial', parentesco: 'Padre/Madre' });
            setMensaje({ texto: "Niño registrado exitosamente", tipo: 'success' });
            cargarNinos();
            setTimeout(() => setMensaje({ texto: '', tipo: '' }), 3000);
        } catch (err) { 
            console.error("Error al registrar niño", err);
            setMensaje({ texto: "Error al registrar el niño", tipo: 'error' });
        }
    };

    const handleAnamnesis = (id_nino) => {
        const nino = ninos.find(n => String(n.id_nino) === String(id_nino));
        if (!nino) {
            console.error('Niño seleccionado no encontrado:', id_nino);
            return;
        }
        setSelectedNino(nino);
        setShowAnamnesis(true);
    };

    const handleBackFromAnamnesis = () => {
        setShowAnamnesis(false);
        setSelectedNino(null);
        cargarNinos(); 
    };

    const handleIniciarEvaluacion = async (nino) => {
        try {
            const response = await iniciarEvaluacion(nino.id_nino);
            
            if (response.status === "error" || response.puede_evaluar === false) {
                setMensaje({ texto: response.mensaje, tipo: 'warning' });
                
                if (response.id_evaluacion_existente) {
                    const quiereVer = window.confirm(
                        `${response.mensaje}\n\n¿Desea ver los resultados de la evaluación anterior?`
                    );
                    if (quiereVer) {
                        setSelectedNino(nino);
                        setIdEvaluacionActual(response.id_evaluacion_existente);
                        setShowResultados(true);
                    }
                }
                return;
            }
            
            setSelectedNino(nino);
            setIdEvaluacionActual(response.id_evaluacion);
            setShowEvaluacion(true);
            
            setMensaje({ texto: response.mensaje, tipo: 'success' });
            setTimeout(() => setMensaje({ texto: '', tipo: '' }), 3000);
            
        } catch (error) {
            console.error('Error al iniciar evaluación:', error);
            setMensaje({ texto: "Error al iniciar la sesión de evaluación", tipo: 'error' });
        }
    };

    const handleVerResultados = (nino) => {
        if (nino.evaluaciones && nino.evaluaciones.length > 0) {
            setSelectedNino(nino);
            setEvaluacionesDisponibles(JSON.parse(nino.evaluaciones));
            setMostrarSelectorEvaluacion(true);
        } else if (nino.ultima_eval_id) {
            setSelectedNino(nino);
            setIdEvaluacionActual(nino.ultima_eval_id);
            setShowResultados(true);
        } else {
            setMensaje({ texto: 'No hay evaluaciones previas para este niño.', tipo: 'error' });
        }
    };

    const handleSeleccionarEvaluacion = (id_ev) => {
        setIdEvaluacionActual(id_ev);
        setMostrarSelectorEvaluacion(false);
        setShowResultados(true);
    };

    const handleExplicacion = (nino) => {
        if (!nino.ultima_eval_id) {
            setMensaje({ texto: 'No hay evaluaciones previas para explicar.', tipo: 'error' });
            return;
        }
        setNinoParaExplicacion(nino);
        setShowExplicacion(true);
    };

    // =========================================================
    // RENDERIZADO CONDICIONAL
    // =========================================================

    if (showAnamnesis) {
        return (
            <AnamnesisForm
                id_nino={selectedNino?.id_nino}
                nombre={selectedNino?.nombre}
                onFinish={handleBackFromAnamnesis}
            />
        );
    }

    if (showEvaluacion) {
        return (
            <div style={styles.container}>
                <button style={styles.btnAction} onClick={() => setShowEvaluacion(false)}>⬅ Volver al Panel</button>
                <EvaluacionFonetica 
                    idNino={selectedNino?.id_nino} 
                    idEvaluacion={idEvaluacionActual}
                    onFinish={() => { setShowEvaluacion(false); setShowResultados(true); }}
                />
            </div>
        );
    }

    if (mostrarSelectorEvaluacion) {
        return (
            <div style={styles.container}>
                <button style={styles.btnAction} onClick={() => setMostrarSelectorEvaluacion(false)}>⬅ Volver</button>
                <div style={styles.card}>
                    <h3>Evaluaciones de {selectedNino?.nombre}</h3>
                    <p>Seleccione qué evaluación desea ver:</p>
                    <div style={styles.evaluacionesList}>
                        {evaluacionesDisponibles.map((evalItem, idx) => (
                            <button
                                key={idx}
                                style={styles.evaluacionBtn}
                                onClick={() => handleSeleccionarEvaluacion(evalItem.id_ev)}
                            >
                                {evalItem.tipo} - {evalItem.fecha_formateada || evalItem.fecha}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (showResultados) {
        return (
            <div style={styles.container}>
                <button style={styles.btnAction} onClick={() => setShowResultados(false)}>⬅ Volver al Panel</button>
                <ResultadosDiagnostico 
                    idNino={selectedNino?.id_nino} 
                    idEvaluacion={idEvaluacionActual} 
                />
            </div>
        );
    }

    if (showExplicacion && ninoParaExplicacion) {
        return (
            <ModuloExplicativo
                idNino={ninoParaExplicacion.id_nino}
                idEvaluacion={ninoParaExplicacion.ultima_eval_id}
                nombreNino={ninoParaExplicacion.nombre}
                onClose={() => {
                    setShowExplicacion(false);
                    setNinoParaExplicacion(null);
                }}
            />
        );
    }

    // =========================================================
    // RENDERIZADO PRINCIPAL DEL DASHBOARD
    // =========================================================
    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h2>Bienvenido, {usuario.nombre}</h2>
                <p>Gestión de pacientes infantiles y evaluaciones</p>
                <button onClick={onLogout} style={styles.btnLogout}>Cerrar Sesión</button>
            </header>

            {mensaje.texto && (
                <div style={{
                    ...styles.mensaje, 
                    backgroundColor: mensaje.tipo === 'success' ? '#d4edda' : mensaje.tipo === 'warning' ? '#fff3cd' : '#f8d7da', 
                    color: mensaje.tipo === 'success' ? '#155724' : mensaje.tipo === 'warning' ? '#856404' : '#721c24'
                }}>
                    {mensaje.texto}
                </div>
            )}

            <section style={styles.card}>
                <h3 style={styles.cardTitle}>Registrar Nuevo Niño</h3>
                <form onSubmit={handleRegister} style={styles.form}>
                    <input style={styles.input} placeholder="Nombre del niño" value={nuevoNino.nombre} onChange={e => setNuevoNino({...nuevoNino, nombre: e.target.value})} required />
                    <input style={styles.input} type="date" value={nuevoNino.f_nac} onChange={e => setNuevoNino({...nuevoNino, f_nac: e.target.value})} required />
                    <p style={styles.ayudaFecha}>
                        📅 El niño debe tener al menos 5 años para ser evaluado
                    </p>
                    <select style={styles.input} value={nuevoNino.genero} onChange={e => setNuevoNino({...nuevoNino, genero: e.target.value})}>
                        <option value="M">Masculino</option>
                        <option value="F">Femenino</option>
                    </select>
                    <select style={styles.input} value={nuevoNino.escolaridad} onChange={e => setNuevoNino({...nuevoNino, escolaridad: e.target.value})}>
                        <option value="Inicial">Inicial</option>
                        <option value="Primaria">Primaria</option>
                        <option value="Secundaria">Secundaria</option>
                    </select>
                    <select style={styles.input} value={nuevoNino.parentesco} onChange={e => setNuevoNino({...nuevoNino, parentesco: e.target.value})}>
                        <option value="Padre/Madre">Padre/Madre</option>
                        <option value="Abuelo/a">Abuelo/a</option>
                        <option value="Tío/a">Tío/a</option>
                        <option value="Otro">Otro</option>
                    </select>
                    <button type="submit" style={styles.btnPrimary}>Añadir Niño</button>
                </form>
            </section>

            <section style={styles.listSection}>
                <h3>Mis Niños Registrados</h3>
                <div style={styles.grid}>
                    {ninos.map(nino => (
                        <div key={nino.id_nino} style={styles.ninoCard}>
                            <h4>{nino.nombre}</h4>
                            <p style={styles.info}>Escolaridad: {nino.escolaridad}</p>
                            
                            {/* INDICADOR DE REEVALUACIÓN */}
                            {nino.tiene_evaluaciones > 0 && nino.puede_reevaluar === false && (
                                <div style={styles.alertaReevaluacion}>
                                    ⏳ Próxima reevaluación en {nino.meses_restantes || 3} meses
                                    <div style={styles.progressBarContainer}>
                                        <div style={{
                                            ...styles.progressBarFill,
                                            width: `${((3 - (nino.meses_restantes || 3)) / 3) * 100}%`
                                        }} />
                                    </div>
                                </div>
                            )}
                            
                            {nino.tiene_evaluaciones > 0 && nino.puede_reevaluar === true && (
                                <div style={styles.alertaReevaluacionLista}>
                                    ✅ ¡Ya puede ser reevaluado!
                                </div>
                            )}
                            
                            <div style={styles.actions}>
                                {!nino.anamnesis_completa ? (
                                    <button style={styles.btnAction} onClick={() => handleAnamnesis(nino.id_nino)}>
                                        📋 Realizar Anamnesis
                                    </button>
                                ) : (
                                    <>
                                        <button 
                                            style={nino.puede_reevaluar !== false ? styles.btnEval : styles.btnEvalDisabled}
                                            onClick={() => (nino.puede_reevaluar !== false) && handleIniciarEvaluacion(nino)}
                                            disabled={nino.puede_reevaluar === false}
                                        >
                                            {nino.tiene_evaluaciones === 0 ? '🎯 Iniciar Evaluación' : '🔄 Iniciar Reevaluación'}
                                        </button>
                                        {nino.tiene_evaluaciones > 0 && (
                                            <>
                                                <button style={styles.btnExplica} onClick={() => handleVerResultados(nino)}>
                                                    📊 Ver Resultados
                                                </button>
                                                <button style={styles.btnExplicacion} onClick={() => handleExplicacion(nino)}>
                                                    💬 Modulo Explicativo
                                                </button>
                                            </>
                                        )}
                                    </>
                                )}
                            </div>
                            
                            {/* Botón para ver progreso completo */}
                            {nino.tiene_evaluaciones >= 1 && (
                                <button 
                                    style={styles.btnProgreso}
                                    onClick={() => onVerProgreso(nino)}
                                >
                                    📈 Ver progreso completo
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
};

const styles = {
    container: { padding: '40px', backgroundColor: '#f4f7f6', minHeight: '100vh' },
    header: { marginBottom: '30px', borderBottom: '2px solid #2c3e50', paddingBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
    mensaje: { padding: '10px 15px', borderRadius: '6px', marginBottom: '20px', fontWeight: 'bold' },
    card: { backgroundColor: '#fff', padding: '20px', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)', marginBottom: '30px' },
    cardTitle: { margin: '0 0 15px 0', fontSize: '18px', color: '#34495e' },
    form: { display: 'flex', gap: '10px', flexWrap: 'wrap' },
    input: { padding: '10px', borderRadius: '6px', border: '1px solid #ddd', flex: 1, minWidth: '150px' },
    ayudaFecha: { fontSize: '11px', color: '#6c757d', marginTop: '4px', marginBottom: '0', width: '100%' },
    btnPrimary: { padding: '10px 20px', backgroundColor: '#2c3e50', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' },
    ninoCard: { backgroundColor: '#fff', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #3498db', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' },
    info: { fontSize: '13px', color: '#7f8c8d', margin: '5px 0 15px 0' },
    actions: { display: 'flex', flexDirection: 'column', gap: '8px' },
    btnAction: { backgroundColor: '#f39c12', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnEval: { backgroundColor: '#27ae60', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnEvalDisabled: { backgroundColor: '#95a5a6', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'not-allowed' },
    btnExplica: { backgroundColor: '#8e44ad', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnExplicacion: { backgroundColor: '#3498db', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnProgreso: { backgroundColor: '#3498db', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer', marginTop: '10px', width: '100%' },
    btnLogout: { backgroundColor: '#e74c3c', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', fontSize: '14px' },
    alertaReevaluacion: { backgroundColor: '#fff3cd', color: '#856404', padding: '8px 12px', borderRadius: '8px', fontSize: '12px', marginBottom: '10px' },
    alertaReevaluacionLista: { backgroundColor: '#d4edda', color: '#155724', padding: '8px 12px', borderRadius: '8px', fontSize: '12px', marginBottom: '10px' },
    progressBarContainer: { backgroundColor: '#e0e0e0', borderRadius: '10px', height: '6px', marginTop: '8px', overflow: 'hidden' },
    progressBarFill: { backgroundColor: '#f39c12', height: '100%', borderRadius: '10px', transition: 'width 0.5s ease' },
    evaluacionesList: { display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '15px' },
    evaluacionBtn: { backgroundColor: '#3498db', color: '#fff', border: 'none', padding: '10px', borderRadius: '6px', cursor: 'pointer', textAlign: 'left' }
};

export default TutorDashboard;