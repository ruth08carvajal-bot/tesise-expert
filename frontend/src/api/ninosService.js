import axios from 'axios';
import { API_ENDPOINTS } from '../config';

export const registrarNino = async (ninoData) => {
    try {
        const response = await axios.post(`${API_ENDPOINTS.ninos}/registrar-nino`, ninoData);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data.detail : "Error al registrar niño";
    }
};

export const obtenerNinos = async (id_tut) => {
    try {
        const response = await axios.get(`${API_ENDPOINTS.ninos}/mis-ninos/${id_tut}`);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data.detail : "Error al obtener niños";
    }
};