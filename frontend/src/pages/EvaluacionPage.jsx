import React, { useState, useEffect } from 'react';
import EvaluacionFonetica from '../components/Evaluacion/EvaluacionFonetica';
import { iniciarEvaluacion } from '../api/evaluacionService';

const EvaluacionPage = () => {
    // Estos IDs normalmente vienen del Login o de la selección del niño
    const idNino = 1;
    const [idEvaluacion, setIdEvaluacion] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const iniciarSesionEvaluacion = async () => {
            try {
                const response = await iniciarEvaluacion(idNino);
                setIdEvaluacion(response.id_evaluacion);
            } catch (error) {
                console.error('Error al iniciar evaluación:', error);
                alert('Error al iniciar la sesión de evaluación');
            } finally {
                setLoading(false);
            }
        };

        iniciarSesionEvaluacion();
    }, [idNino]);

    if (loading) {
        return <div className="container"><p>Iniciando sesión de evaluación...</p></div>;
    }

    if (!idEvaluacion) {
        return <div className="container"><p>Error: No se pudo iniciar la evaluación</p></div>;
    }

    return (
        <div className="container">
            <h1>Sesión de Evaluación Directa</h1>
            <p>Basado en la anamnesis previa, realizaremos las siguientes pruebas:</p>

            <EvaluacionFonetica
                idNino={idNino}
                idEvaluacion={idEvaluacion}
            />
        </div>
    );
};