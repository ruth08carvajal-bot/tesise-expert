import React, { useState, useEffect } from 'react';
import { obtenerPlan, enviarAudioEvaluacion, enviarValorFuzzy } from '../../api/evaluacionService';

// =========================================================
// RECURSOS Y CONFIGURACIÓN DE EJERCICIOS
// =========================================================

const recursosEjercicios = {
    // === EJERCICIOS DE AUDIO (MFCC) ===
    "Palabra Corta": {
        tipo: "mfcc",
        imagen: "/images/ejercicios/palabra_corta.png",
        video: null,
        instruccion: "Repite la palabra que escuchas",
        ejemplo: "🗣️ Di: Ratón, Sol, Flor",
        consejo: "Habla claro y despacio"
    },
    "Palabra Compleja": {
        tipo: "mfcc",
        imagen: "/images/ejercicios/palabra_compleja.png",
        video: null,
        instruccion: "Repite la palabra larga",
        ejemplo: "🗣️ Di: Ferrocarril, Trabalenguas",
        consejo: "Intenta decir cada sílaba"
    },
    "Fonemas Aislados": {
        tipo: "mfcc",
        imagen: "/images/ejercicios/fonemas.png",
        video: null,
        instruccion: "Haz el sonido como un animal",
        ejemplo: "🗣️ Haz: ssss (serpiente), rrrr (moto), chchch (tren)",
        consejo: "Mírate en el espejo"
    },
    "Ruta Fonológica": {
        tipo: "mfcc",
        imagen: "/images/ejercicios/lectura.png",
        video: null,
        instruccion: "Lee la palabra inventada",
        ejemplo: "📖 Lee: Pli-tro, Fla-gon",
        consejo: "Separa las sílabas"
    },

    // === EJERCICIOS CON VIDEO Y EVALUACIÓN MANUAL ===
    "Soplo Controlado": {
        tipo: "video_fuzzy",
        imagen: null,
        video: "/videos/ejercicios/soplo.mp4",
        instruccion: "Observa el video y luego evalúa",
        ejemplo: "💨 Sopla como si apagaras una vela",
        consejo: "Toma aire profundo antes de soplar",
        preguntaEvaluacion: "¿Cómo fue su soplo?"
    },
    "Praxias Linguales": {
        tipo: "video_fuzzy",
        imagen: null,
        video: "/videos/ejercicios/praxias.mp4",
        instruccion: "Observa el video y luego evalúa",
        ejemplo: "👅 Saca la lengua y toca tu nariz",
        consejo: "Hazlo frente al espejo",
        preguntaEvaluacion: "¿Cómo fue su ejecución?"
    },
    "El Ritmo de Osito": {
        tipo: "video_fuzzy",
        imagen: null,
        video: "/videos/ejercicios/ritmo.mp4",
        instruccion: "Observa el video y luego evalúa",
        ejemplo: "👏 Sigue el ritmo: golpe-golpe-golpe",
        consejo: "Escucha atentamente",
        preguntaEvaluacion: "¿Cómo fue su desempeño?"
    },

    // === EJERCICIOS SOCIALES ===
    "Turnos de Habla": {
        tipo: "fuzzy",
        imagen: "/images/ejercicios/turnos.png",
        video: null,
        instruccion: "Observa y evalúa",
        ejemplo: "💬 ¿El niño respeta los turnos al conversar?",
        consejo: "Respeta cuando otros hablan",
        preguntaEvaluacion: "¿Cómo fue su respeto de turnos?"
    },

    // === EJERCICIOS DE SELECCIÓN DE IMÁGENES ===
    "Emociones": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "feliz", imagen: "/images/emociones/feliz.png", texto: "Feliz", correcta: true, valor: 1.0 },
            { id: "triste", imagen: "/images/emociones/triste.png", texto: "Triste", correcta: false, valor: 0.0 },
            { id: "enojado", imagen: "/images/emociones/enojado.png", texto: "Enojado", correcta: false, valor: 0.0 },
            { id: "sorprendido", imagen: "/images/emociones/sorprendido.png", texto: "Sorprendido", correcta: false, valor: 0.0 }
        ],
        pregunta: "¿Cómo se siente el niño en la imagen?",
        instruccion: "Haz clic en la emoción correcta",
        consejo: "Observa la expresión de la cara",
        preguntaEvaluacion: "¿Seleccionó la emoción correcta?"
    },
    "Absurdos Visuales": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "sol_llorando", imagen: "/images/absurdos/sol_llorando.png", texto: "El sol está llorando", correcta: true, valor: 1.0 },
            { id: "sol_normal", imagen: "/images/absurdos/sol_normal.png", texto: "El sol normal", correcta: false, valor: 0.0 }
        ],
        pregunta: "¿Qué está mal en esta imagen?",
        instruccion: "Haz clic en la imagen que tiene algo absurdo",
        consejo: "Piensa qué es normal y qué no",
        preguntaEvaluacion: "¿Identificó el absurdo?"
    },
    "Categorización": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "manzana", imagen: "/images/categorias/manzana.png", texto: "Manzana", correcta: false, valor: 0.0 },
            { id: "perro", imagen: "/images/categorias/perro.png", texto: "Perro", correcta: true, valor: 1.0 },
            { id: "platano", imagen: "/images/categorias/platano.png", texto: "Plátano", correcta: false, valor: 0.0 },
            { id: "uva", imagen: "/images/categorias/uva.png", texto: "Uva", correcta: false, valor: 0.0 }
        ],
        pregunta: "¿Cuál de estos NO es una fruta?",
        instruccion: "Haz clic en el que no pertenece",
        consejo: "Piensa en la categoría de cada dibujo",
        preguntaEvaluacion: "¿Identificó correctamente?"
    },
    "Opuestos": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "grande", imagen: "/images/opuestos/grande.png", texto: "Grande", correcta: false, valor: 0.0 },
            { id: "pequeno", imagen: "/images/opuestos/pequeno.png", texto: "Pequeño", correcta: true, valor: 1.0 }
        ],
        pregunta: "Si el elefante es GRANDE, ¿qué es el ratón?",
        instruccion: "Haz clic en la respuesta correcta",
        consejo: "Piensa en lo opuesto a grande",
        preguntaEvaluacion: "¿Seleccionó la opción correcta?"
    },
    "Orientación Letras": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "b", imagen: "/images/letras/b.png", texto: "Letra B", correcta: false, valor: 0.0 },
            { id: "d", imagen: "/images/letras/d.png", texto: "Letra D", correcta: true, valor: 1.0 }
        ],
        pregunta: "Selecciona la letra D",
        instruccion: "Haz clic en la letra correcta",
        consejo: "La D tiene la pancita a la derecha",
        preguntaEvaluacion: "¿Seleccionó la letra correcta?"
    },
    "Completar Frase": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "come", imagen: "/images/frases/come.png", texto: "come", correcta: true, valor: 1.0 },
            { id: "duerme", imagen: "/images/frases/duerme.png", texto: "duerme", correcta: false, valor: 0.0 },
            { id: "corre", imagen: "/images/frases/corre.png", texto: "corre", correcta: false, valor: 0.0 }
        ],
        pregunta: "El perro _____ un hueso",
        instruccion: "Haz clic en la palabra que completa la frase",
        consejo: "Piensa en lo que hace un perro con un hueso",
        preguntaEvaluacion: "¿Completó la frase correctamente?"
    },
    "Reglas Ortográficas": {
        tipo: "seleccion_fuzzy",
        imagenes: [
            { id: "volar", imagen: "/images/ortografia/volar.png", texto: "Volar", correcta: true, valor: 1.0 },
            { id: "bolar", imagen: "/images/ortografia/bolar.png", texto: "Bolar", correcta: false, valor: 0.0 }
        ],
        pregunta: "¿Cuál está escrita correctamente?",
        instruccion: "Haz clic en la palabra bien escrita",
        consejo: "Recuerda que 'volar' lleva V",
        preguntaEvaluacion: "¿Seleccionó la ortografía correcta?"
    }
};

const EvaluacionFonetica = ({ idNino, idEvaluacion, onFinish }) => {
    const [ejercicios, setEjercicios] = useState([]);
    const [indiceActual, setIndiceActual] = useState(0);
    const [grabando, setGrabando] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);
    const [resultado, setResultado] = useState(null);
    const [valorFuzzy, setValorFuzzy] = useState(0.5);
    const [error, setError] = useState(null);
    const [mostrarAyuda, setMostrarAyuda] = useState(false);
    const [seleccionImagen, setSeleccionImagen] = useState(null);
    const [mostrarSliderEvaluacion, setMostrarSliderEvaluacion] = useState(false);

    useEffect(() => {
        const cargarDatos = async () => {
            try {
                const data = await obtenerPlan(idNino);
                if (!data || !data.plan_adaptativo) {
                    setError("No se pudieron cargar los ejercicios");
                    setEjercicios([]);
                    return;
                }
                setEjercicios(data.plan_adaptativo);
            } catch (err) { 
                console.error("Error al cargar plan:", err);
                setError("Error al conectar con el servidor");
            }
        };

        if (idNino) cargarDatos();
    }, [idNino]);

    const iniciarGrabacion = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const tipos = ['audio/webm', 'audio/webm;codecs=opus'];
            let tipoSeleccionado = null;

            for (let tipo of tipos) {
                if (MediaRecorder.isTypeSupported(tipo)) {
                    tipoSeleccionado = tipo;
                    break;
                }
            }

            if (!tipoSeleccionado) {
                alert('Tu navegador no soporta grabación de audio');
                return;
            }

            const recorder = new MediaRecorder(stream, { mimeType: tipoSeleccionado });
            const trozosAudio = [];
            
            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) trozosAudio.push(e.data);
            };

            recorder.onstop = async () => {
                const audioBlob = new Blob(trozosAudio, { type: tipoSeleccionado });
                const formData = new FormData();
                
                formData.append('audio', audioBlob, `grabacion.webm`);
                formData.append('id_nino', idNino);
                formData.append('id_evaluacion', idEvaluacion);
                formData.append('fonema_objetivo', ejercicioActual.id_hecho_objetivo);
                
                try {
                    const res = await enviarAudioEvaluacion(formData);
                    setResultado(res);
                } catch (error) { 
                    console.error("Error:", error);
                    alert("Error al analizar la voz. Intenta nuevamente."); 
                }
                
                stream.getTracks().forEach(track => track.stop());
            };

            recorder.start();
            setMediaRecorder(recorder);
            setGrabando(true);

        } catch (err) {
            console.error("Error micrófono:", err);
            alert("No se pudo acceder al micrófono. Verifica los permisos.");
        }
    };

    const detenerGrabacion = () => {
        if (mediaRecorder && grabando) {
            mediaRecorder.stop();
            setGrabando(false);
        }
    };

    const enviarCalificacionFuzzy = async (valor = valorFuzzy) => {
        const datos = {
            id_nino: idNino, 
            id_evaluacion: idEvaluacion,
            id_hecho: ejercicioActual.id_hecho_objetivo, 
            valor: parseFloat(valor)
        };
        try {
            const res = await enviarValorFuzzy(datos);
            setResultado(res);
            setMostrarSliderEvaluacion(false);
        } catch (error) { 
            console.error("Error:", error);
            alert("Error al guardar la calificación"); 
        }
    };

    const manejarSeleccionImagen = (imagen) => {
        setSeleccionImagen(imagen.id);
        enviarCalificacionFuzzy(imagen.valor);
    };

    const manejarSiguiente = () => {
        if (indiceActual + 1 < ejercicios.length) {
            setIndiceActual(indiceActual + 1);
            setResultado(null);
            setValorFuzzy(0.5);
            setMostrarAyuda(false);
            setSeleccionImagen(null);
            setMostrarSliderEvaluacion(false);
        } else { 
            onFinish(); 
        }
    };

    const progreso = ((indiceActual + 1) / ejercicios.length) * 100;

    if (error) {
        return (
            <div style={styles.errorContainer}>
                <p>{error}</p>
                <button style={styles.backButton} onClick={onFinish}>← Volver</button>
            </div>
        );
    }

    if (ejercicios.length === 0) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.spinner}></div>
                <p>Cargando ejercicios...</p>
            </div>
        );
    }

    const ejercicioActual = ejercicios[indiceActual];
    if (!ejercicioActual) {
        return <div style={styles.errorContainer}><p>No hay ejercicios disponibles</p></div>;
    }

    const recurso = recursosEjercicios[ejercicioActual.nombre_ejercicio] || {
        tipo: "fuzzy",
        imagen: "/images/ejercicios/default.png",
        video: null,
        instruccion: ejercicioActual.descripcion_instrucciones,
        ejemplo: ejercicioActual.descripcion_instrucciones,
        consejo: "¡Tú puedes!",
        preguntaEvaluacion: "¿Cómo evaluarías este ejercicio?"
    };

    const tipoEjercicio = recurso.tipo || (ejercicioActual.tipo_apoyo === 'MFCC' ? 'mfcc' : 'fuzzy');

    // Renderizar según tipo de ejercicio
    const renderizarContenido = () => {
        switch (tipoEjercicio) {
            case 'mfcc':
                return (
                    <div style={styles.audioSection}>
                        {!grabando ? (
                            <button onClick={iniciarGrabacion} style={styles.recordButton}>
                                🎤 Iniciar Grabación
                            </button>
                        ) : (
                            <button onClick={detenerGrabacion} style={styles.stopButton}>
                                🛑 Detener y Evaluar
                            </button>
                        )}
                        {grabando && (
                            <div style={styles.recordingIndicator}>
                                <span style={styles.recordingDot}></span>
                                Grabando...
                            </div>
                        )}
                    </div>
                );

            case 'video_fuzzy':
                return (
                    <div style={styles.videoFuzzySection}>
                        <video 
                            src={recurso.video} 
                            style={styles.videoPlayer}
                            controls
                            poster={recurso.imagen}
                        />
                        {!resultado && !mostrarSliderEvaluacion && (
                            <button 
                                onClick={() => setMostrarSliderEvaluacion(true)} 
                                style={styles.evaluateButton}
                            >
                                📊 Evaluar actividad
                            </button>
                        )}
                        {mostrarSliderEvaluacion && (
                            <div style={styles.sliderEvaluacion}>
                                <p style={styles.preguntaEvaluacion}>{recurso.preguntaEvaluacion || "¿Cómo fue su desempeño?"}</p>
                                {renderizarSliderFuzzy()}
                            </div>
                        )}
                    </div>
                );

            case 'seleccion_fuzzy':
                return (
                    <div style={styles.seleccionSection}>
                        <p style={styles.preguntaEvaluacion}>{recurso.pregunta}</p>
                        <div style={styles.imagenesGrid}>
                            {recurso.imagenes.map((img) => (
                                <div 
                                    key={img.id}
                                    style={{
                                        ...styles.imagenCard,
                                        ...(seleccionImagen === img.id ? styles.imagenCardSeleccionada : {})
                                    }}
                                    onClick={() => manejarSeleccionImagen(img)}
                                >
                                    <img src={img.imagen} alt={img.texto} style={styles.imagenSeleccion} />
                                    <p>{img.texto}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            default: // fuzzy con slider mejorado
                return renderizarSliderFuzzy();
        }
    };

    const renderizarSliderFuzzy = () => {
        if (resultado) return null;
        
        return (
            <div style={styles.fuzzySection}>
                <p style={styles.preguntaEvaluacion}>{recurso.preguntaEvaluacion || "¿Cómo evaluarías este ejercicio?"}</p>
                <div style={styles.sliderContainer}>
                    <span>😞 Muy mal</span>
                    <div style={styles.sliderWrapper}>
                        <input 
                            type="range" 
                            min="0" 
                            max="1" 
                            step="0.1" 
                            value={valorFuzzy} 
                            onChange={(e) => setValorFuzzy(parseFloat(e.target.value))} 
                            style={styles.slider}
                        />
                        <div style={styles.sliderMarkers}>
                            {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map((val) => (
                                <span key={val} style={styles.sliderMarker}>|</span>
                            ))}
                        </div>
                        <div style={styles.sliderLabels}>
                            {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map((val) => (
                                <span key={val} style={styles.sliderLabel}>{val}</span>
                            ))}
                        </div>
                    </div>
                    <span>🎉 Excelente</span>
                </div>
                <p style={styles.fuzzyValue}>Puntaje seleccionado: {Math.round(valorFuzzy * 100)}%</p>
                <button onClick={() => enviarCalificacionFuzzy(valorFuzzy)} style={styles.submitButton}>
                    ✓ Guardar Calificación
                </button>
            </div>
        );
    };

    return (
        <div style={styles.container}>
            {/* Barra de progreso */}
            <div style={styles.progressSection}>
                <div style={styles.progressBarContainer}>
                    <div style={{ ...styles.progressBarFill, width: `${progreso}%` }} />
                </div>
                <p style={styles.progressText}>
                    Ejercicio {indiceActual + 1} de {ejercicios.length}
                </p>
            </div>

            {/* Tarjeta del ejercicio */}
            <div style={styles.card}>
                <div style={styles.cardHeader}>
                    <h2 style={styles.title}>{ejercicioActual.nombre_ejercicio}</h2>
                    <button 
                        style={styles.helpButton} 
                        onClick={() => setMostrarAyuda(!mostrarAyuda)}
                        title="Ver consejo"
                    >
                        💡
                    </button>
                </div>

                {/* Imagen o video de demostración */}
                {(recurso.imagen || recurso.video) && tipoEjercicio !== 'seleccion_fuzzy' && (
                    <div style={styles.mediaContainer}>
                        {recurso.video ? (
                            <video 
                                src={recurso.video} 
                                style={styles.media}
                                controls
                                poster={recurso.imagen}
                            />
                        ) : (
                            <img 
                                src={recurso.imagen} 
                                alt={ejercicioActual.nombre_ejercicio}
                                style={styles.media}
                                onError={(e) => {
                                    e.target.src = "/images/ejercicios/default.png";
                                }}
                            />
                        )}
                    </div>
                )}

                <p style={styles.instruccion}>{recurso.instruccion}</p>
                <p style={styles.example}>📋 {recurso.ejemplo}</p>

                {mostrarAyuda && (
                    <div style={styles.tipContainer}>
                        <p style={styles.tipText}>💡 {recurso.consejo}</p>
                    </div>
                )}
                
                {/* Área interactiva según tipo */}
                <div style={styles.practiceArea}>
                    {renderizarContenido()}
                </div>

                {/* Resultado */}
                {resultado && (
                    <div style={styles.resultContainer}>
                        <div style={styles.resultBadge(resultado.similitud_detectada)}>
                            {resultado.similitud_detectada >= 0.7 ? '🎉' : resultado.similitud_detectada >= 0.4 ? '📈' : '💪'} 
                            {Math.round(resultado.similitud_detectada * 100)}%
                        </div>
                        <p style={styles.resultMessage}>
                            {resultado.similitud_detectada >= 0.7 ? '¡Excelente! Sigue así.' :
                             resultado.similitud_detectada >= 0.4 ? '¡Buen intento! Sigue practicando.' :
                             '¡No te rindas! Cada intento cuenta.'}
                        </p>
                        <button onClick={manejarSiguiente} style={styles.nextButton}>
                            {indiceActual + 1 === ejercicios.length ? '🏆 Finalizar' : '➡ Siguiente'}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const styles = {
    container: {
        maxWidth: '700px',
        margin: '0 auto',
        padding: '20px'
    },
    progressSection: {
        marginBottom: '20px'
    },
    progressBarContainer: {
        backgroundColor: 'rgba(255,255,255,0.3)',
        borderRadius: '10px',
        height: '8px',
        overflow: 'hidden'
    },
    progressBarFill: {
        backgroundColor: '#27ae60',
        height: '100%',
        borderRadius: '10px',
        transition: 'width 0.3s ease'
    },
    progressText: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.8)',
        marginTop: '8px',
        textAlign: 'center'
    },
    card: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '20px',
        padding: '25px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
    },
    cardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '15px'
    },
    title: {
        fontSize: '22px',
        color: '#2c3e50',
        margin: 0
    },
    helpButton: {
        backgroundColor: '#f0f0f0',
        border: 'none',
        width: '35px',
        height: '35px',
        borderRadius: '50%',
        cursor: 'pointer',
        fontSize: '18px'
    },
    mediaContainer: {
        backgroundColor: '#f5f5f5',
        borderRadius: '15px',
        padding: '15px',
        marginBottom: '20px',
        textAlign: 'center'
    },
    media: {
        maxWidth: '100%',
        maxHeight: '180px',
        borderRadius: '10px'
    },
    instruccion: {
        fontSize: '15px',
        fontWeight: 'bold',
        color: '#2c3e50',
        marginBottom: '8px',
        textAlign: 'center'
    },
    example: {
        fontSize: '14px',
        color: '#3498db',
        backgroundColor: '#e8f4fd',
        padding: '10px',
        borderRadius: '10px',
        textAlign: 'center',
        marginBottom: '15px'
    },
    tipContainer: {
        backgroundColor: '#fff3cd',
        padding: '10px',
        borderRadius: '10px',
        marginBottom: '20px'
    },
    tipText: {
        margin: 0,
        fontSize: '13px',
        color: '#856404'
    },
    practiceArea: {
        marginTop: '20px'
    },
    audioSection: {
        textAlign: 'center'
    },
    recordButton: {
        backgroundColor: '#e74c3c',
        color: 'white',
        border: 'none',
        padding: '15px 30px',
        borderRadius: '50px',
        cursor: 'pointer',
        fontSize: '18px',
        fontWeight: 'bold'
    },
    stopButton: {
        backgroundColor: '#f39c12',
        color: 'white',
        border: 'none',
        padding: '15px 30px',
        borderRadius: '50px',
        cursor: 'pointer',
        fontSize: '18px',
        fontWeight: 'bold'
    },
    recordingIndicator: {
        marginTop: '15px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        color: '#e74c3c'
    },
    recordingDot: {
        width: '12px',
        height: '12px',
        backgroundColor: '#e74c3c',
        borderRadius: '50%',
        animation: 'pulse 1s infinite'
    },
    videoFuzzySection: {
        textAlign: 'center'
    },
    videoPlayer: {
        width: '100%',
        maxHeight: '300px',
        borderRadius: '15px',
        marginBottom: '15px'
    },
    evaluateButton: {
        backgroundColor: '#3498db',
        color: 'white',
        border: 'none',
        padding: '12px 24px',
        borderRadius: '50px',
        cursor: 'pointer',
        fontSize: '16px',
        fontWeight: 'bold',
        marginTop: '10px'
    },
    sliderEvaluacion: {
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#f8f9fa',
        borderRadius: '15px'
    },
    seleccionSection: {
        textAlign: 'center'
    },
    imagenesGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '15px',
        marginBottom: '15px'
    },
    imagenCard: {
        backgroundColor: 'white',
        borderRadius: '15px',
        padding: '15px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        border: '2px solid transparent',
        textAlign: 'center'
    },
    imagenCardSeleccionada: {
        border: '2px solid #27ae60',
        backgroundColor: '#e8f5e9',
        transform: 'scale(1.02)'
    },
    imagenSeleccion: {
        width: '100%',
        maxHeight: '100px',
        objectFit: 'contain',
        marginBottom: '10px'
    },
    fuzzySection: {
        textAlign: 'center'
    },
    preguntaEvaluacion: {
        fontSize: '15px',
        fontWeight: 'bold',
        color: '#2c3e50',
        marginBottom: '15px'
    },
    sliderContainer: {
        display: 'flex',
        alignItems: 'center',
        gap: '15px',
        flexWrap: 'wrap',
        justifyContent: 'center',
        marginBottom: '10px'
    },
    sliderWrapper: {
        flex: 1,
        minWidth: '250px'
    },
    slider: {
        width: '100%',
        height: '6px',
        borderRadius: '5px',
        background: '#ddd',
        WebkitAppearance: 'none'
    },
    sliderMarkers: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '0 2px',
        marginTop: '4px',
        fontSize: '10px',
        color: '#999'
    },
    sliderLabels: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '0 2px',
        marginTop: '2px',
        fontSize: '9px',
        color: '#888'
    },
    sliderMarker: {
        fontSize: '10px'
    },
    sliderLabel: {
        fontSize: '9px'
    },
    fuzzyValue: {
        fontSize: '16px',
        fontWeight: 'bold',
        color: '#2c3e50',
        marginBottom: '15px'
    },
    submitButton: {
        backgroundColor: '#27ae60',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '25px',
        cursor: 'pointer'
    },
    resultContainer: {
        marginTop: '25px',
        padding: '20px',
        backgroundColor: '#e8f4fd',
        borderRadius: '15px',
        textAlign: 'center'
    },
    resultBadge: (puntaje) => ({
        fontSize: '36px',
        fontWeight: 'bold',
        color: puntaje >= 0.7 ? '#27ae60' : puntaje >= 0.4 ? '#f39c12' : '#e74c3c',
        marginBottom: '10px'
    }),
    resultMessage: {
        fontSize: '14px',
        color: '#555',
        marginBottom: '15px'
    },
    nextButton: {
        backgroundColor: '#3498db',
        color: 'white',
        border: 'none',
        padding: '12px 25px',
        borderRadius: '25px',
        cursor: 'pointer',
        fontWeight: 'bold'
    },
    errorContainer: {
        textAlign: 'center',
        padding: '40px',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderRadius: '20px',
        margin: '20px'
    },
    loadingContainer: {
        textAlign: 'center',
        padding: '40px',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderRadius: '20px'
    },
    spinner: {
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite',
        margin: '0 auto 15px'
    },
    backButton: {
        marginTop: '15px',
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '8px',
        cursor: 'pointer'
    }
};

// Añadir keyframes
const styleSheet = document.createElement("style");
styleSheet.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
`;
document.head.appendChild(styleSheet);

export default EvaluacionFonetica;