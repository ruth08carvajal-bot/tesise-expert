import React, { useState, useEffect } from 'react';
import { obtenerPlan, enviarAudioEvaluacion, enviarValorFuzzy } from '../../api/evaluacionService';

const EvaluacionFonetica = ({ idNino, idEvaluacion, onFinish }) => {
    const [ejercicios, setEjercicios] = useState([]);
    const [indiceActual, setIndiceActual] = useState(0);
    const [grabando, setGrabando] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);
    const [resultado, setResultado] = useState(null);
    const [valorFuzzy, setValorFuzzy] = useState(0.5);

    useEffect(() => {
        const cargarDatos = async () => {
            try {
                const data = await obtenerPlan(idNino);
                setEjercicios(data.plan_evaluacion);
            } catch (err) { console.error(err); }
        };
        if (idNino) cargarDatos();
    }, [idNino]);

    const ejercicioActual = ejercicios[indiceActual];

    const iniciarGrabacion = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Intentamos grabar en WAV si el navegador lo soporta, sino webm
        const tipos = ['audio/wav', 'audio/webm;codecs=opus', 'audio/webm'];
        let tipoSeleccionado = null;
        for (let tipo of tipos) {
            if (MediaRecorder.isTypeSupported(tipo)) {
                tipoSeleccionado = tipo;
                break;
            }
        }
        if (!tipoSeleccionado) {
            alert('No se soporta grabación de audio en este navegador');
            return;
        }
        const recorder = new MediaRecorder(stream, { mimeType: tipoSeleccionado });
        const trozosAudio = [];
        
        recorder.ondataavailable = (e) => {
            if (e.data.size > 0) trozosAudio.push(e.data);
        };

        recorder.onstop = async () => {
            // Creamos el Blob con el tipo correcto
            const audioBlob = new Blob(trozosAudio, { type: tipoSeleccionado });
            const extension = tipoSeleccionado.includes('wav') ? 'wav' : 'webm';
            const formData = new FormData();
            
            formData.append('audio', audioBlob, `grabacion.${extension}`);
            formData.append('id_nino', idNino);
            formData.append('id_evaluacion', idEvaluacion);
            formData.append('fonema_objetivo', ejercicioActual.id_hecho_objetivo);
            
            try {
                const res = await enviarAudioEvaluacion(formData);
                setResultado(res);
            } catch (error) { 
                console.error("Error en el envío:", error);
                alert("Error en el analisis de voz"); 
            }
        };

        recorder.start();
        setMediaRecorder(recorder);
        setGrabando(true);
    };

    const enviarCalificacionFuzzy = async () => {
        const datos = {
            id_nino: idNino, id_evaluacion: idEvaluacion,
            id_hecho: ejercicioActual.id_hecho_objetivo, valor: valorFuzzy
        };
        try {
            const res = await enviarValorFuzzy(datos);
            setResultado(res);
        } catch (error) { alert("Error en envío manual"); }
    };

    const manejarSiguiente = () => {
        if (indiceActual + 1 < ejercicios.length) {
            setIndiceActual(indiceActual + 1);
            setResultado(null);
            setValorFuzzy(0.5);
        } else { onFinish(); }
    };

    if (ejercicios.length === 0) return <p>Cargando ejercicios...</p>;

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h2>{ejercicioActual.nombre_ejercicio}</h2>
                <p>{ejercicioActual.descripcion_instrucciones}</p>
                {ejercicioActual.tipo_apoyo === 'MFCC' ? (
                    <div style={styles.section}>
                        {!grabando ? 
                            <button onClick={iniciarGrabacion} style={styles.btnStart}>🎤 Iniciar Grabación</button> : 
                            <button onClick={() => { mediaRecorder.stop(); setGrabando(false); }} style={styles.btnStop}>🛑 Detener y Evaluar</button>
                        }
                    </div>
                ) : (
                    <div style={styles.section}>
                        <input type="range" min="0" max="1" step="0.1" value={valorFuzzy} onChange={(e) => setValorFuzzy(e.target.value)} />
                        <p>Calidad percibida: {Math.round(valorFuzzy * 100)}%</p>
                        {!resultado && <button onClick={enviarCalificacionFuzzy} style={styles.btnNext}>Guardar Calificación</button>}
                    </div>
                )}
                {resultado && (
                    <div style={styles.resultBox}>
                        <p style={{fontWeight: 'bold'}}>Resultado: {(resultado.similitud_detectada * 100).toFixed(1)}% de precisión</p>
                        <button onClick={manejarSiguiente} style={styles.btnNext}>Siguiente Ejercicio</button>
                    </div>
                )}
            </div>
        </div>
    );
};

const styles = {
    container: { display: 'flex', justifyContent: 'center', padding: '20px' },
    card: { background: '#f9f9f9', padding: '30px', borderRadius: '15px', boxShadow: '0 4px 8px rgba(0,0,0,0.1)', textAlign: 'center', width: '100%', maxWidth: '500px' },
    section: { margin: '20px 0' },
    btnStart: { backgroundColor: '#4CAF50', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '5px', cursor: 'pointer' },
    btnStop: { backgroundColor: '#f44336', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '5px', cursor: 'pointer' },
    btnNext: { backgroundColor: '#2196F3', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '5px', cursor: 'pointer', marginTop: '10px' },
    resultBox: { marginTop: '20px', padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '10px' }
};

export default EvaluacionFonetica;