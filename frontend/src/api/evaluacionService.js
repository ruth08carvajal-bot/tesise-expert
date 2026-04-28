// api/evaluacionService.js
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8003/evaluacion';

// =========================================================
// EVALUACIÓN PRINCIPAL
// =========================================================

export const obtenerPlan = async (id_nino) => {
    const response = await axios.get(`${API_URL}/plan-evaluacion/${id_nino}`);
    return response.data;
};

export const enviarAudioEvaluacion = async (formData) => {
    const response = await axios.post(`${API_URL}/evaluar-fonema`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const enviarValorFuzzy = async (datos) => {
    const response = await axios.post(`${API_URL}/evaluar-manual`, datos);
    return response.data;
};

export const iniciarEvaluacion = async (id_nino) => {
    const formData = new FormData();
    formData.append('id_nino', id_nino);
    const response = await axios.post(`${API_URL}/iniciar-evaluacion`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const obtenerResultadosDiagnostico = async (id_nino, id_evaluacion) => {
    const response = await axios.get(`${API_URL}/ejecutar-diagnostico/${id_nino}/${id_evaluacion}`);
    return response.data;
};

export const finalizarEvaluacion = async (id_nino, id_evaluacion) => {
    const response = await axios.post(`${API_URL}/finalizar-evaluacion`, {
        id_nino: id_nino,
        id_evaluacion: id_evaluacion
    });
    return response.data;
};

// =========================================================
// DATOS Y REPORTES
// =========================================================

export const obtenerDatosEvaluacion = async (id_nino, id_evaluacion) => {
    const response = await axios.get(`${API_URL}/datos-evaluacion/${id_nino}/${id_evaluacion}`);
    return response.data;
};

export const generarReportePDF = async (id_nino, id_evaluacion) => {
    const response = await axios.post(`${API_URL}/generar-reporte-pdf`, {
        id_nino: id_nino,
        id_evaluacion: id_evaluacion
    }, {
        responseType: 'blob'
    });
    return response.data;
};

export const generarReportePDFConDatos = async (id_nino, id_evaluacion, datos) => {
    const response = await axios.post(`${API_URL}/generar-reporte-pdf`, {
        id_nino: id_nino,
        id_evaluacion: id_evaluacion,
        datos: datos
    }, {
        responseType: 'blob'
    });
    return response.data;
};

// =========================================================
// HISTORIAL
// =========================================================

export const obtenerHistorialEvaluaciones = async (id_nino) => {
    const response = await axios.get(`${API_URL}/historial-evaluaciones/${id_nino}`);
    return response.data;
};

export const agregarNotas = async (id_evaluacion, notas) => {
    const formData = new FormData();
    formData.append('id_evaluacion', id_evaluacion);
    formData.append('notas', notas);
    
    const response = await axios.post(`${API_URL}/agregar-notas`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};