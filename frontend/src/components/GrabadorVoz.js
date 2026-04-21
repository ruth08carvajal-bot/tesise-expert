import React, { useState, useRef } from 'react';
import axios from 'axios';

const GrabadorVoz = ({ idNino, idEvaluacion, fonemaObjetivo }) => {
    const [grabando, setGrabando] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [resultado, setResultado] = useState(null);
    const mediaRecorder = useRef(null);
    const chunks = useRef([]);

    const iniciarGrabacion = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder.current = new MediaRecorder(stream);
        chunks.current = [];

        mediaRecorder.current.ondataavailable = (e) => chunks.current.push(e.data);
        mediaRecorder.current.onstop = async () => {
            const blob = new Blob(chunks.current, { type: 'audio/wav' });
            const url = URL.createObjectURL(blob);
            setAudioUrl(url);
            enviarAlBackend(blob);
        };

        mediaRecorder.current.start();
        setGrabando(true);
    };

    const detenerGrabacion = () => {
        mediaRecorder.current.stop();
        setGrabando(false);
    };

    const enviarAlBackend = async (audioBlob) => {
        const formData = new FormData();
        formData.append('id_nino', idNino);
        formData.append('id_evaluacion', idEvaluacion);
        formData.append('fonema_objetivo', fonemaObjetivo);
        formData.append('audio', audioBlob, 'grabacion.wav');

        try {
            const resp = await axios.post('http://localhost:8003/evaluacion/evaluar-fonema', formData);
            setResultado(resp.data);
        } catch (error) {
            console.error("Error al evaluar:", error);
        }
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '10px' }}>
            <h3>Practicando fonema: /{fonemaObjetivo}/</h3>
            
            {!grabando ? (
                <button onClick={iniciarGrabacion} style={{ backgroundColor: 'green', color: 'white' }}>
                    🎤 Iniciar Micrófono
                </button>
            ) : (
                <button onClick={detenerGrabacion} style={{ backgroundColor: 'red', color: 'white' }}>
                    🛑 Detener y Evaluar
                </button>
            )}

            {resultado && (
                <div style={{ marginTop: '20px' }}>
                    <p><strong>Similitud:</strong> {(resultado.similitud_detectada * 100).toFixed(2)}%</p>
                    <h4>Diagnósticos encontrados:</h4>
                    {resultado.diagnosticos.map((d, index) => (
                        <div key={index} style={{ background: '#f0f0f0', padding: '10px', marginBottom: '5px' }}>
                            <strong>{d.nombre_diag}</strong> (Certeza: {d.fc_total})
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default GrabadorVoz;