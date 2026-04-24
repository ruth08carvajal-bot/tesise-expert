import React, { useState, useEffect } from 'react';
import { obtenerPlan, enviarAudioEvaluacion, enviarValorFuzzy } from '../../api/evaluacionService';

const EvaluacionFonetica = ({ idNino, idEvaluacion, onFinish }) => {
    const [ejercicios, setEjercicios] = useState([]);
    const [indiceActual, setIndiceActual] = useState(0);
    const [grabando, setGrabando] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);
    const [resultado, setResultado] = useState(null);
    const [valorFuzzy, setValorFuzzy] = useState(0.5);

        // carga de ejercicios con nuevo formato 23/04/26
    const [error, setError] = useState(null);

    useEffect(() => {
        const cargarDatos = async () => {
            try {
                console.log("🔍 Cargando plan para niño:", idNino);

                const data = await obtenerPlan(idNino);

                console.log("📦 Respuesta backend:", data);
               // NUEVO: el backend ahora devuelve un plan adaptativo con formato actualizado 23/04/26
               if (!data || !data.plan_adaptativo) {
                    setError("El backend no devolvió plan_adaptativo");
                    setEjercicios([]);
                    return;
                }

                setEjercicios(data.plan_adaptativo);

                //setEjercicios(data.plan_evaluacion);
                // NUEVO: ahora el backend devuelve un plan adaptativo con formato actualizado 23/04/26
                setEjercicios(data.plan_adaptativo || []);

            } catch (err) { 
                console.error("❌ Error al cargar plan:", err);
                setError("Error al conectar con el servidor");
            }
        };

        if (idNino) cargarDatos();
    }, [idNino]);// hasta aquí nueva carga de ejercicios con formato actualizado

    const iniciarGrabacion = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const tipos = ['audio/wav', 'audio/webm;codecs=opus', 'audio/webm'];
            let tipoSeleccionado = null;

            for (let tipo of tipos) {
                if (MediaRecorder.isTypeSupported(tipo)) {
                    tipoSeleccionado = tipo;
                    break;
                }
            }

            if (!tipoSeleccionado) {
                alert('Navegador no compatible con grabación de audio');
                return;
            }

            // --- VARIABLES LOCALES DENTRO DEL SCOPE ---
            const recorder = new MediaRecorder(stream, { mimeType: tipoSeleccionado });
            const trozosAudio = [];
            
            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) trozosAudio.push(e.data);
            };

            recorder.onstop = async () => {
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
                    alert("Error en el análisis de voz"); 
                }
                
                // Apagar micrófono
                stream.getTracks().forEach(track => track.stop());
            };

            // Iniciar grabación
            recorder.start();
            setMediaRecorder(recorder);
            setGrabando(true);

        } catch (err) {
            console.error("Error micrófono:", err);
            alert("No se pudo acceder al micrófono.");
        }
    };

    const detenerGrabacion = () => {
        if (mediaRecorder && grabando) {
            mediaRecorder.stop();
            setGrabando(false);
        }
    };

    const enviarCalificacionFuzzy = async () => {
        const datos = {
            id_nino: idNino, 
            id_evaluacion: idEvaluacion,
            id_hecho: ejercicioActual.id_hecho_objetivo, 
            valor: parseFloat(valorFuzzy)
        };
        try {
            const res = await enviarValorFuzzy(datos);
            setResultado(res);
        } catch (error) { 
            alert("Error en envío manual"); 
        }
    };

    const manejarSiguiente = () => {
        if (indiceActual + 1 < ejercicios.length) {
            setIndiceActual(indiceActual + 1);
            setResultado(null);
            setValorFuzzy(0.5);
        } else { 
            onFinish(); 
        }
    };
    // NUEVO: manejo de errores y estado de carga con mensajes más claros
    if (error) {
        return <p style={{color: 'red'}}>{error}</p>;
    }

    if (ejercicios.length === 0) {
        return <p>Cargando ejercicios del sistema experto...</p>;
    } //fin de nuevo manejo de errores y estado de carga
    const ejercicioActual = ejercicios[indiceActual];
    //inicio de nuevo manejo de errores y estado de carga para ejercicios
    if (!ejercicioActual) {
        return <p>No hay ejercicios disponibles</p>;
    }//fin de nuevo manejo de errores y estado de carga para ejercicios

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h2>{ejercicioActual.nombre_ejercicio}</h2>
                <p>{ejercicioActual.descripcion_instrucciones}</p>
                
                {ejercicioActual.tipo_apoyo === 'MFCC' ? (
                    <div style={styles.section}>
                        {!grabando ? (
                            <button onClick={iniciarGrabacion} style={styles.btnStart}>🎤 Iniciar Grabación</button>
                        ) : (
                            <button onClick={detenerGrabacion} style={styles.btnStop}>🛑 Detener y Evaluar</button>
                        )}
                    </div>
                ) : (
                    <div style={styles.section}>
                        <input 
                            type="range" min="0" max="1" step="0.1" 
                            value={valorFuzzy} 
                            onChange={(e) => setValorFuzzy(e.target.value)} 
                        />
                        <p>Calidad: {Math.round(valorFuzzy * 100)}%</p>
                        {!resultado && <button onClick={enviarCalificacionFuzzy} style={styles.btnNext}>Guardar Calificación</button>}
                    </div>
                )}

                {resultado && (
                    <div style={styles.resultBox}>
                        <p style={{fontWeight: 'bold'}}>
                            Precisión detectada: {(resultado.similitud_detectada * 100).toFixed(1)}%
                        </p>
                        <button onClick={manejarSiguiente} style={styles.btnNext}>Siguiente</button>
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