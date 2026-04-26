import React, { useState, useEffect, useCallback } from 'react';
import { registrarNino, obtenerNinos } from '../api/ninosService';
import AnamnesisForm from './AnamnesisForm';
import EvaluacionFonetica from '../components/Evaluacion/EvaluacionFonetica';
import ResultadosDiagnostico from '../components/Evaluacion/ResultadosDiagnostico';
import { iniciarEvaluacion } from '../api/evaluacionService';

const TutorDashboard = ({ usuario, onLogout }) => {
    const [ninos, setNinos] = useState([]);
    const [nuevoNino, setNuevoNino] = useState({
        nombre: '', f_nac: '', genero: 'M', escolaridad: 'Inicial', parentesco: 'Padre/Madre'
    });
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [showAnamnesis, setShowAnamnesis] = useState(false);
    const [selectedNino, setSelectedNino] = useState(null);

    // --- NUEVOS ESTADOS PARA EVALUACIÓN ---
    const [showEvaluacion, setShowEvaluacion] = useState(false);
    const [showResultados, setShowResultados] = useState(false);
    const [idEvaluacionActual, setIdEvaluacionActual] = useState(null);

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
        console.log('handleAnamnesis called with id_nino:', id_nino);
        const nino = ninos.find(n => String(n.id_nino) === String(id_nino));
        console.log('Found nino:', nino);
        if (!nino) {
            console.error('Niño seleccionado no encontrado:', id_nino, ninos);
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

    // --- FUNCIONES PARA MANEJAR EVALUACIÓN Y RESULTADOS ---
    const handleIniciarEvaluacion = async (nino) => {
        try {
            const response = await iniciarEvaluacion(nino.id_nino);
            setSelectedNino(nino);
            setIdEvaluacionActual(response.id_evaluacion);
            setShowEvaluacion(true);
        } catch (error) {
            console.error('Error al iniciar evaluación:', error);
            setMensaje({ texto: "Error al iniciar la sesión de evaluación", tipo: 'error' });
        }
    };

    const handleVerResultados = (nino) => {
        if (!nino.ultima_eval_id) {
            setMensaje({ texto: 'No hay evaluaciones previas disponibles para este niño.', tipo: 'error' });
            return;
        }
        setSelectedNino(nino);
        setIdEvaluacionActual(nino.ultima_eval_id);
        setShowResultados(true);
    };

    // --- RENDERIZADO CONDICIONAL ---

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

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h2>Bienvenido, {usuario.nombre}</h2>
                <p>Gestión de pacientes infantiles y evaluaciones</p>
                <button onClick={onLogout} style={styles.btnLogout}>Cerrar Sesión</button>
            </header>

            {mensaje.texto && (
                <div style={{...styles.mensaje, backgroundColor: mensaje.tipo === 'success' ? '#d4edda' : '#f8d7da', color: mensaje.tipo === 'success' ? '#155724' : '#721c24'}}>
                    {mensaje.texto}
                </div>
            )}

            <section style={styles.card}>
                <h3 style={styles.cardTitle}>Registrar Nuevo Niño</h3>
                <form onSubmit={handleRegister} style={styles.form}>
                    <input style={styles.input} placeholder="Nombre del niño" value={nuevoNino.nombre} onChange={e => setNuevoNino({...nuevoNino, nombre: e.target.value})} required />
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
                            
                            <div style={styles.actions}>
                                {!nino.anamnesis_completa ? (
                                    <button style={styles.btnAction} onClick={() => handleAnamnesis(nino.id_nino)}>Realizar Anamnesis</button>
                                ) : (
                                    <button style={styles.btnEval} onClick={() => handleIniciarEvaluacion(nino)}>Iniciar Evaluación</button>
                                )}
                                {nino.tiene_evaluaciones && (
                                    <button style={styles.btnExplica} onClick={() => handleVerResultados(nino)}>Ver Resultados</button>
                                )}
                            </div>
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
    btnPrimary: { padding: '10px 20px', backgroundColor: '#2c3e50', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' },
    ninoCard: { backgroundColor: '#fff', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #3498db', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' },
    info: { fontSize: '13px', color: '#7f8c8d', margin: '5px 0 15px 0' },
    actions: { display: 'flex', flexDirection: 'column', gap: '8px' },
    btnAction: { backgroundColor: '#f39c12', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnEval: { backgroundColor: '#27ae60', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnExplica: { backgroundColor: '#8e44ad', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' },
    btnLogout: { backgroundColor: '#e74c3c', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', fontSize: '14px' }
};

export default TutorDashboard;