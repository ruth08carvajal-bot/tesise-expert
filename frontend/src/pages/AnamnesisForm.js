import React, { useState, useEffect } from 'react';

const AnamnesisForm = ({ id_nino, nombre, onFinish }) => {
    const [preguntas, setPreguntas] = useState([]);
    const [edad, setEdad] = useState(0);
    const [nombreNino, setNombreNino] = useState(nombre || 'Niño');
    const [respuestas, setRespuestas] = useState({}); // {id_hecho: valor}
    const [loading, setLoading] = useState(true);
    const [mensaje, setMensaje] = useState('');

    useEffect(() => {
        const cargarPreguntas = async () => {
            if (!id_nino) {
                setPreguntas([]);
                setLoading(false);
                setMensaje('No se proporcionó el niño para la anamnesis.');
                return;
            }

            setLoading(true);
            setMensaje('');

            console.log('Cargando preguntas para niño:', id_nino);
            try {
                const response = await fetch(`http://127.0.0.1:8003/anamnesis/preguntas-anamnesis/${id_nino}`);
                console.log('Response status:', response.status);
                if (!response.ok) {
                    const errorBody = await response.text();
                    console.error('Error body:', errorBody);
                    throw new Error(`HTTP ${response.status}: ${errorBody}`);
                }
                const data = await response.json();
                console.log('Data received:', data);
                setPreguntas(data.preguntas || []);
                setEdad(data.edad_nino || 0);
                setNombreNino(data.nombre_nino || nombre || 'Niño');
            } catch (error) {
                console.error('Error cargando preguntas:', error);
                setMensaje('Error al cargar las preguntas. Intenta de nuevo.');
            } finally {
                setLoading(false);
            }
        };

        cargarPreguntas();
    }, [id_nino, nombre]);

    const handleOptionChange = (id_hecho, valor) => {
        setRespuestas({ ...respuestas, [id_hecho]: valor });
    };

    const guardarAnamnesis = async () => {
        const preguntasSinResponder = preguntas.filter(p => respuestas[p.id_hecho] === undefined);
        if (preguntasSinResponder.length > 0) {
            alert(`Debes responder todas las preguntas antes de guardar. Faltan ${preguntasSinResponder.length} preguntas.`);
            return;
        }

        const hechos_presentes = preguntas
            .filter(p => respuestas[p.id_hecho] === 1)
            .map(p => p.id_hecho);

        const payload = {
            id_nino,
            hechos_presentes
        };

        try {
            const response = await fetch('http://127.0.0.1:8003/anamnesis/guardar-anamnesis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error('Error al guardar la anamnesis');
            }

            await response.json();
            onFinish();
        } catch (error) {
            console.error('Error:', error);
            setMensaje('Hubo un error al guardar la anamnesis. Inténtalo de nuevo.');
        }
    };

    if (loading) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.spinner}></div>
                <p>Cargando preguntas...</p>
            </div>
        );
    }

    if (!id_nino) {
        return (
            <div style={styles.container}>
                <p style={styles.errorMessage}>No se encontró el niño seleccionado. Vuelve al dashboard y elige un niño válido.</p>
                <button style={styles.backButton} onClick={onFinish}>Volver</button>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={styles.title}>Anamnesis para {nombreNino}</h1>
                <p style={styles.subtitle}>Edad: {edad} años</p>
            </div>

            {mensaje && (
                <div style={styles.errorMessage}>{mensaje}</div>
            )}

            {preguntas.length === 0 ? (
                <div style={styles.noQuestions}>
                    <p>No hay preguntas disponibles para este niño en este momento.</p>
                    <button style={styles.backButton} onClick={onFinish}>Volver</button>
                </div>
            ) : (
                <div style={styles.formList}>
                    {preguntas.map(p => (
                        <div key={p.id_hecho} style={styles.preguntaCard}>
                            <div>
                                <p style={styles.questionText}>{p.descripcion_hecho}</p>
                                <p style={styles.category}>Categoría: {p.categoria}</p>
                            </div>
                            <div style={styles.options}>
                                <button
                                    type="button"
                                    onClick={() => handleOptionChange(p.id_hecho, 1)}
                                    style={respuestas[p.id_hecho] === 1 ? styles.btnActive : styles.btn}
                                >Presente</button>
                                <button
                                    type="button"
                                    onClick={() => handleOptionChange(p.id_hecho, 0)}
                                    style={respuestas[p.id_hecho] === 0 ? styles.btnActive : styles.btn}
                                >Ausente</button>
                            </div>
                        </div>
                    ))}
                    <button type="button" onClick={guardarAnamnesis} style={styles.saveBtn}>Finalizar y Guardar</button>
                    <button type="button" onClick={onFinish} style={styles.backButton}>Volver</button>
                </div>
            )}
        </div>
    );
};

const styles = {
    container: {
        padding: '30px',
        maxWidth: '900px',
        margin: 'auto',
        backgroundColor: '#f8f9fa',
        minHeight: '100vh',
        fontFamily: 'Arial, sans-serif'
    },
    loadingContainer: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        color: '#555'
    },
    spinner: {
        border: '4px solid rgba(0,0,0,0.1)',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite'
    },
    header: {
        textAlign: 'center',
        marginBottom: '25px'
    },
    title: {
        margin: '0 0 10px 0',
        fontSize: '32px',
        color: '#2c3e50'
    },
    subtitle: {
        margin: 0,
        color: '#7f8c8d',
        fontSize: '18px'
    },
    errorMessage: {
        backgroundColor: '#f8d7da',
        color: '#721c24',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
    },
    noQuestions: {
        textAlign: 'center',
        padding: '30px',
        backgroundColor: '#fff',
        borderRadius: '12px',
        border: '1px solid #e9ecef'
    },
    formList: {
        display: 'flex',
        flexDirection: 'column',
        gap: '15px'
    },
    preguntaCard: {
        backgroundColor: '#fff',
        padding: '20px',
        borderRadius: '10px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
        border: '1px solid #e9ecef'
    },
    questionText: {
        fontSize: '16px',
        fontWeight: 'bold',
        margin: '0 0 10px 0'
    },
    category: {
        margin: 0,
        color: '#6c757d',
        fontSize: '14px'
    },
    options: {
        display: 'flex',
        gap: '12px'
    },
    btn: {
        padding: '10px 18px',
        borderRadius: '6px',
        border: '2px solid #007bff',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold',
        backgroundColor: '#fff',
        color: '#007bff'
    },
    btnActive: {
        padding: '10px 18px',
        borderRadius: '6px',
        border: 'none',
        backgroundColor: '#007bff',
        color: '#fff',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold'
    },
    saveBtn: {
        width: '100%',
        padding: '15px',
        backgroundColor: '#28a745',
        color: '#fff',
        border: 'none',
        borderRadius: '8px',
        marginTop: '10px',
        fontWeight: 'bold',
        cursor: 'pointer',
        fontSize: '16px'
    },
    backButton: {
        width: '100%',
        padding: '15px',
        backgroundColor: '#6c757d',
        color: '#fff',
        border: 'none',
        borderRadius: '8px',
        marginTop: '10px',
        fontWeight: 'bold',
        cursor: 'pointer',
        fontSize: '16px'
    }
};

export default AnamnesisForm;