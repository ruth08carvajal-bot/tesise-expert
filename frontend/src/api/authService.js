import axios from 'axios';
import { API_ENDPOINTS } from '../config';

export const login = async (username, password) => {
    try {
        const response = await axios.post(`${API_ENDPOINTS.auth}/login`, {
            username,
            password
        });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data.detail : "Error de conexión";
    }
};
// registrar nuevo usuario (tutor)
export const register = async (formData) => {
    try {
        const response = await axios.post(`${API_ENDPOINTS.auth}/register`, {
            nombre_completo: formData.nombre_completo,
            username: formData.username,
            password: formData.password,
            email: formData.email,
            celular: formData.celular,
            ocupacion: formData.ocupacion,
            zona: formData.zona
        });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data.detail : "Error al registrar";
    }
};