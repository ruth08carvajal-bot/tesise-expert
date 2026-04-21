import axios from 'axios';

const API_URL = 'http://127.0.0.1:8003/ninos';

export const registrarNino = async (ninoData) => {
    try {
        const response = await axios.post(`${API_URL}/registrar-nino`, ninoData);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data.detail : "Error al registrar niño";
    }
};

export const obtenerNinos = async (id_tut) => {
    try {
        const response = await axios.get(`${API_URL}/mis-ninos/${id_tut}`);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data.detail : "Error al obtener niños";
    }
};