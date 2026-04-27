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
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '', mostrar: false });
    const [showAnamnesis, setShowAnamnesis] = useState(false);
    const [selectedNino, setSelectedNino] = useState(null);
    const [showEvaluacion, setShowEvaluacion] = useState(false);
    const [showResultados, setShowResultados] = useState(false);
    const [idEvaluacionActual, setIdEvaluacionActual] = useState(null);
    const [mostrarSelectorEvaluacion, setMostrarSelectorEvaluacion] = useState(false);
    const [evaluacionesDisponibles, setEvaluacionesDisponibles] = useState([]);
    const [showExplicacion, setShowExplicacion] = useState(false);
    const [ninoParaExplicacion, setNinoParaExplicacion] = useState(null);
    
    // Estados para UI
    const [mostrarFormulario, setMostrarFormulario] = useState(false);
    // eslint-disable-next-line no-unused-vars
    const [cargando, setCargando] = useState(false);

    const cargarNinos = useCallback(async () => {
        if (!usuario || !usuario.id_tut) return;
        setCargando(true);
        try {
            const data = await obtenerNinos(usuario.id_tut);
            setNinos(data);
        } catch (err) {
            console.error("Error al cargar niños", err);
            setMensaje({ texto: "Error al cargar la lista de niños", tipo: 'error', mostrar: true });
            setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 3000);
        } finally {
            setCargando(false);
        }
    }, [usuario]);

    useEffect(() => {
        cargarNinos();
    }, [cargarNinos]);

    const calcularEdad = (fechaNac) => {
        const hoy = new Date();
        const nac = new Date(fechaNac);
        let edad = hoy.getFullYear() - nac.getFullYear();
        const mesDiff = hoy.getMonth() - nac.getMonth();
        if (mesDiff < 0 || (mesDiff === 0 && hoy.getDate() < nac.getDate())) edad--;
        return edad;
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        const fechaNacimiento = new Date(nuevoNino.f_nac);
        const hoy = new Date();
        let edad = hoy.getFullYear() - fechaNacimiento.getFullYear();
        const mesDiff = hoy.getMonth() - fechaNacimiento.getMonth();
        if (mesDiff < 0 || (mesDiff === 0 && hoy.getDate() < fechaNacimiento.getDate())) edad--;
        
        if (edad < 5) {
            setMensaje({ 
                texto: `El niño debe tener al menos 5 años para ser evaluado. Edad actual: ${edad} años.`, 
                tipo: 'error', 
                mostrar: true 
            });
            return;
        }
        
        try {
            await registrarNino({ ...nuevoNino, id_tut: usuario.id_tut });
            setNuevoNino({ nombre: '', f_nac: '', genero: 'M', escolaridad: 'Inicial', parentesco: 'Padre/Madre' });
            setMensaje({ texto: "Niño registrado exitosamente", tipo: 'success', mostrar: true });
            setMostrarFormulario(false);
            cargarNinos();
            setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 3000);
        } catch (err) { 
            console.error("Error al registrar niño", err);
            setMensaje({ texto: "Error al registrar el niño", tipo: 'error', mostrar: true });
            setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 3000);
        }
    };

    const handleAnamnesis = (id_nino) => {
        const nino = ninos.find(n => String(n.id_nino) === String(id_nino));
        if (!nino) return;
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
                setMensaje({ texto: response.mensaje, tipo: 'warning', mostrar: true });
                setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 4000);
                return;
            }
            setSelectedNino(nino);
            setIdEvaluacionActual(response.id_evaluacion);
            setShowEvaluacion(true);
        } catch (error) {
            console.error('Error al iniciar evaluación:', error);
            setMensaje({ texto: "Error al iniciar la sesión de evaluación", tipo: 'error', mostrar: true });
            setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 3000);
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
            setMensaje({ texto: 'No hay evaluaciones previas para este niño.', tipo: 'error', mostrar: true });
            setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 3000);
        }
    };

    const handleSeleccionarEvaluacion = (id_ev) => {
        setIdEvaluacionActual(id_ev);
        setMostrarSelectorEvaluacion(false);
        setShowResultados(true);
    };

    const handleExplicacion = (nino) => {
        if (!nino.ultima_eval_id) {
            setMensaje({ texto: 'No hay evaluaciones previas para explicar.', tipo: 'error', mostrar: true });
            setTimeout(() => setMensaje({ texto: '', tipo: '', mostrar: false }), 3000);
            return;
        }
        setNinoParaExplicacion(nino);
        setShowExplicacion(true);
    };

    // Funciones para navegación
    const handleVolverDeResultados = () => {
        setShowResultados(false);
        setSelectedNino(null);
        setIdEvaluacionActual(null);
    };

    const handleVolverDeEvaluacion = () => {
        setShowEvaluacion(false);
        setSelectedNino(null);
        setIdEvaluacionActual(null);
    };

    const handleVolverDeSelector = () => {
        setMostrarSelectorEvaluacion(false);
        setSelectedNino(null);
    };

    // Renderizado condicional
    if (showAnamnesis) {
        return <AnamnesisForm id_nino={selectedNino?.id_nino} nombre={selectedNino?.nombre} onFinish={handleBackFromAnamnesis} />;
    }
    
    if (showEvaluacion) {
        return (
            <div style={styles.fullScreenContainer}>
                <div style={styles.videoBackgroundFull}>
                    <video autoPlay loop muted playsInline style={styles.videoFull}>
                        <source src="/videos/fondo.mp4" type="video/mp4" />
                    </video>
                </div>
                <button style={styles.backButtonModal} onClick={handleVolverDeEvaluacion}>← Volver</button>
                <div style={styles.fullScreenContent}>
                    <EvaluacionFonetica 
                        idNino={selectedNino?.id_nino} 
                        idEvaluacion={idEvaluacionActual} 
                        onFinish={() => { 
                            setShowEvaluacion(false); 
                            setShowResultados(true); 
                        }} 
                    />
                </div>
            </div>
        );
    }
    
    if (mostrarSelectorEvaluacion) {
        return (
            <div style={styles.selectorContainer}>
                {/* Video de fondo */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundImage: 'url("/images/fondo_cero.png")',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    zIndex: 0
                }} />
                
                {/* Contenido */}
                <div style={styles.selectorContent}>
                    <button style={styles.closeButton} onClick={handleVolverDeSelector}>
                        ✕ Cerrar
                    </button>
                    
                    <div style={styles.selectorCard}>
                        <h3 style={styles.selectorTitle}>Evaluaciones de {selectedNino?.nombre}</h3>
                        <p style={styles.selectorSubtitle}>Seleccione la evaluación que desea ver:</p>
                        
                        <div style={styles.evaluacionesList}>
                            {evaluacionesDisponibles.map((evalItem, idx) => (
                                <button
                                    key={idx}
                                    style={styles.evaluacionItem}
                                    onClick={() => handleSeleccionarEvaluacion(evalItem.id_ev)}
                                >
                                    <span style={styles.evaluacionTipo}>{evalItem.tipo}</span>
                                    <span style={styles.evaluacionFecha}>{evalItem.fecha_formateada || evalItem.fecha}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    if (showResultados) {
        return (
            <ResultadosDiagnostico 
                idNino={selectedNino?.id_nino} 
                idEvaluacion={idEvaluacionActual}
                onBack={handleVolverDeResultados}
            />
        );
    }
    
    if (showExplicacion && ninoParaExplicacion) {
        return (
            <ModuloExplicativo
                idNino={ninoParaExplicacion.id_nino}
                idEvaluacion={ninoParaExplicacion.ultima_eval_id}
                nombreNino={ninoParaExplicacion.nombre}
                onClose={() => { setShowExplicacion(false); setNinoParaExplicacion(null); }}
            />
        );
    }

    // Renderizado principal
    return (
        <div style={styles.container}>
            {/* Video de fondo */}
            <video autoPlay loop muted playsInline style={styles.videoBackground}>
                <source src="/videos/fondo.mp4" type="video/mp4" />
            </video>

            {/* Modal de mensaje */}
            {mensaje.mostrar && (
                <div style={styles.modalMensajeOverlay} onClick={() => setMensaje({ ...mensaje, mostrar: false })}>
                    <div style={styles.modalMensajeContainer} onClick={(e) => e.stopPropagation()}>
                        <div style={mensaje.tipo === 'error' ? styles.modalError : mensaje.tipo === 'warning' ? styles.modalWarning : styles.modalSuccess}>
                            <p>{mensaje.texto}</p>
                            <button onClick={() => setMensaje({ ...mensaje, mostrar: false })}>Aceptar</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Contenido principal */}
            <div style={styles.content}>
                {/* Barra superior */}
                <div style={styles.topBar}>
                    <div style={styles.logoArea}>
                        <h1 style={styles.title}>Las Voces del Illimani</h1>
                        <p style={styles.subtitle}>Sistema Experto Fonoaudiológico</p>
                        <p style={styles.welcomeMessage}>Bienvenido, {usuario.nombre}</p>
                    </div>
                    <div style={styles.rightButtons}>
                        <button style={styles.logoutButton} onClick={onLogout}>Cerrar Sesión</button>
                        <button 
                            style={styles.addButton}
                            onClick={() => setMostrarFormulario(!mostrarFormulario)}
                        >
                            {mostrarFormulario ? 'Cancelar' : '+ Añadir Niño'}
                        </button>
                    </div>
                </div>

                {/* Formulario de registro (colapsable, centrado) */}
                {mostrarFormulario && (
                    <div style={styles.formContainer}>
                        <div style={styles.formCard}>
                            <h3>Registrar nuevo niño</h3>
                            <form onSubmit={handleRegister} style={styles.form}>
                                <input style={styles.input} placeholder="Nombre" value={nuevoNino.nombre} onChange={e => setNuevoNino({...nuevoNino, nombre: e.target.value})} required />
                                <input style={styles.input} type="date" value={nuevoNino.f_nac} onChange={e => setNuevoNino({...nuevoNino, f_nac: e.target.value})} required />
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
                                <button type="submit" style={styles.submitButton}>Registrar</button>
                            </form>
                        </div>
                    </div>
                )}

                {/* Lista de niños - columna derecha */}
                <div style={styles.ninosColumn}>
                    <h3 style={styles.ninosTitle}>Mis Niños</h3>
                    {ninos.length === 0 ? (
                        <div style={styles.emptyCard}>
                            <p>No hay niños registrados</p>
                            <p>Haz clic en "+ Añadir Niño"</p>
                        </div>
                    ) : (
                        ninos.map(nino => {
                            const edad = calcularEdad(nino.f_nac);
                            const puedeReevaluar = nino.puede_reevaluar !== false;
                            return (
                                <div key={nino.id_nino} style={styles.ninoCard}>
                                    <div style={styles.ninoHeader}>
                                        <strong style={styles.ninoName}>{nino.nombre}</strong>
                                        <span style={styles.ninoAge}>{edad} años</span>
                                    </div>
                                    <p style={styles.ninoSchool}>📚 {nino.escolaridad}</p>
                                    
                                    {nino.tiene_evaluaciones > 0 && !puedeReevaluar && (
                                        <div style={styles.warningBadge}>
                                            ⏳ Próxima reevaluación en {nino.meses_restantes || 3} meses
                                        </div>
                                    )}
                                    {nino.tiene_evaluaciones > 0 && puedeReevaluar && (
                                        <div style={styles.successBadge}>✅ Listo para reevaluar</div>
                                    )}
                                    
                                    <div style={styles.buttonGroup}>
                                        {!nino.anamnesis_completa ? (
                                            <button style={styles.btnWarning} onClick={() => handleAnamnesis(nino.id_nino)}>📋 Anamnesis</button>
                                        ) : (
                                            <>
                                                <button 
                                                    style={puedeReevaluar ? styles.btnSuccess : styles.btnDisabled} 
                                                    onClick={() => puedeReevaluar && handleIniciarEvaluacion(nino)} 
                                                    disabled={!puedeReevaluar}
                                                >
                                                    {nino.tiene_evaluaciones === 0 ? '🎤 Evaluar' : '🔄 Reevaluar'}
                                                </button>
                                                {nino.tiene_evaluaciones > 0 && (
                                                    <>
                                                        <button style={styles.btnInfo} onClick={() => handleVerResultados(nino)}>📊 Resultados</button>
                                                        <button style={styles.btnProgress} onClick={() => onVerProgreso(nino)}>📈 Progreso</button>
                                                        <button style={styles.btnExpert} onClick={() => handleExplicacion(nino)}>💬 Explicación</button>
                                                    </>
                                                )}
                                            </>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )}
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
        width: '100%',
        height: '100%',
        objectFit: 'cover',
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
        padding: '20px 30px'
    },
    topBar: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '40px'
    },
    logoArea: {
        textAlign: 'left'
    },
    welcomeMessage: {
        fontSize: '14px',
        color: 'rgba(255, 255, 255, 0.9)',
        marginTop: '8px',
        fontWeight: '500',
        textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
    },
    title: {
        fontSize: '28px',
        fontWeight: 'bold',
        color: 'white',
        textShadow: '1px 1px 4px rgba(0,0,0,0.5)',
        margin: 0
    },
    subtitle: {
        fontSize: '14px',
        color: 'rgba(255,255,255,0.8)',
        margin: '5px 0 0',
        textShadow: '1px 1px 2px rgba(0,0,0,0.5)'
    },
    rightButtons: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '8px'
    },
    logoutButton: {
        backgroundColor: 'rgba(61, 57, 105, 0.9)',
        color: 'white',
        border: 'none',
        padding: '8px 20px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        backdropFilter: 'blur(5px)'
    },
    addButton: {
        backgroundColor: 'rgba(102, 169, 109, 0.9)',
        color: 'white',
        border: 'none',
        padding: '8px 20px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontSize: '13px',
        backdropFilter: 'blur(5px)'
    },
    formContainer: {
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '30px'
    },
    formCard: {
        backgroundColor: 'rgb(243, 247, 249)',
        borderRadius: '16px',
        padding: '20px',
        width: '100%',
        maxWidth: '500px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
    },
    input: {
        padding: '10px',
        borderRadius: '8px',
        border: '1px solid #ddd',
        fontSize: '14px'
    },
    submitButton: {
        padding: '10px',
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer'
    },
    ninosColumn: {
        position: 'fixed',
        right: '30px',
        top: '120px',
        width: '320px',
        maxHeight: 'calc(100vh - 150px)',
        overflowY: 'auto',
        backgroundColor: 'rgba(163, 202, 222, 0.6)',
        borderRadius: '16px',
        padding: '15px',
        boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
        backdropFilter: 'blur(5px)'
    },
    ninosTitle: {
        fontSize: '18px',
        color: '#2c3e50',
        margin: '0 0 15px',
        paddingBottom: '8px',
        borderBottom: '2px solid #3498db',
        textAlign: 'center'
    },
    ninoCard: {
        backgroundColor: '#d4e2e87a',
        borderRadius: '12px',
        padding: '12px',
        marginBottom: '12px',
        borderLeft: '4px solid #3498db',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    },
    ninoHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '5px'
    },
    ninoName: {
        fontSize: '16px',
        color: '#2c3e50'
    },
    ninoAge: {
        fontSize: '12px',
        color: '#262829',
        backgroundColor: '#f0f4f8',
        padding: '2px 8px',
        borderRadius: '15px'
    },
    ninoSchool: {
        fontSize: '11px',
        color: '#242626',
        margin: '0 0 10px'
    },
    warningBadge: {
        backgroundColor: '#fff3cd',
        color: '#856404',
        padding: '5px 8px',
        borderRadius: '6px',
        fontSize: '10px',
        marginBottom: '10px',
        textAlign: 'center'
    },
    successBadge: {
        backgroundColor: '#d4edda',
        color: '#155724',
        padding: '5px 8px',
        borderRadius: '6px',
        fontSize: '10px',
        marginBottom: '10px',
        textAlign: 'center'
    },
    buttonGroup: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px',
        marginTop: '8px'
    },
    btnSuccess: {
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        padding: '5px 10px',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '11px'
    },
    btnWarning: {
        backgroundColor: '#f39c12',
        color: 'white',
        border: 'none',
        padding: '5px 10px',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '11px'
    },
    btnInfo: {
        backgroundColor: '#8e44ad',
        color: 'white',
        border: 'none',
        padding: '5px 10px',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '11px'
    },
    btnProgress: {
        backgroundColor: '#1abc9c',
        color: 'white',
        border: 'none',
        padding: '5px 10px',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '11px'
    },
    btnExpert: {
        backgroundColor: '#3498db',
        color: 'white',
        border: 'none',
        padding: '5px 10px',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '11px'
    },
    btnDisabled: {
        backgroundColor: '#95a5a6',
        color: 'white',
        border: 'none',
        padding: '5px 10px',
        borderRadius: '5px',
        cursor: 'not-allowed',
        fontSize: '11px'
    },
    emptyCard: {
        textAlign: 'center',
        padding: '30px',
        color: '#7f8c8d'
    },
    modalMensajeOverlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 2000
    },
    modalMensajeContainer: {
        minWidth: '300px',
        maxWidth: '400px',
        textAlign: 'center'
    },
    modalError: {
        backgroundColor: '#f8d7da',
        color: '#721c24',
        padding: '20px',
        borderRadius: '12px',
        border: '1px solid #f5c6cb'
    },
    modalWarning: {
        backgroundColor: '#fff3cd',
        color: '#856404',
        padding: '20px',
        borderRadius: '12px',
        border: '1px solid #ffeeba'
    },
    modalSuccess: {
        backgroundColor: '#d4edda',
        color: '#155724',
        padding: '20px',
        borderRadius: '12px',
        border: '1px solid #c3e6cb'
    },
    // Estilos para el selector de evaluaciones
    selectorContainer: {
        position: 'relative',
        minHeight: '100vh',
        overflow: 'hidden'
    },
    selectorContent: {
        position: 'relative',
        zIndex: 1,
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px'
    },
    closeButton: {
        position: 'fixed',
        top: '20px',
        right: '20px',
        backgroundColor: 'rgba(231, 76, 60, 0.9)',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '30px',
        cursor: 'pointer',
        fontSize: '14px',
        zIndex: 10,
        backdropFilter: 'blur(5px)'
    },
    selectorCard: {
        backgroundColor: 'rgba(255, 255, 255, 0.92)',
        borderRadius: '20px',
        padding: '30px',
        maxWidth: '450px',
        width: '90%',
        textAlign: 'center',
        backdropFilter: 'blur(5px)',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
    },
    selectorTitle: {
        fontSize: '22px',
        color: '#2c3e50',
        margin: '0 0 10px'
    },
    selectorSubtitle: {
        fontSize: '14px',
        color: '#7f8c8d',
        margin: '0 0 25px'
    },
    evaluacionesList: {
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
    },
    evaluacionItem: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'white',
        border: '1px solid #e0e0e0',
        borderRadius: '12px',
        padding: '14px 20px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        width: '100%'
    },
    evaluacionTipo: {
        fontWeight: 'bold',
        color: '#2c3e50'
    },
    evaluacionFecha: {
        color: '#7f8c8d',
        fontSize: '13px'
    },
    // Estilos para pantalla completa de evaluación
    fullScreenContainer: {
        position: 'relative',
        minHeight: '100vh',
        overflow: 'hidden'
    },
    videoBackgroundFull: {
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        zIndex: 0
    },
    videoFull: {
        width: '100%',
        height: '100%',
        objectFit: 'cover'
    },
    backButtonModal: {
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
        zIndex: 10,
        backdropFilter: 'blur(5px)'
    },
    fullScreenContent: {
        position: 'relative',
        zIndex: 1,
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px'
    }
};

export default TutorDashboard;