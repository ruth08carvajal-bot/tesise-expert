const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8004';

export const API_ENDPOINTS = {
  auth: `${API_BASE_URL}/auth`,
  evaluacion: `${API_BASE_URL}/evaluacion`,
  ejercicios: `${API_BASE_URL}/ejercicios`,
  ninos: `${API_BASE_URL}/ninos`,
  explicacion: `${API_BASE_URL}/explicacion`,
  glosario: `${API_BASE_URL}/glosario`,
  inferencia: `${API_BASE_URL}/inferencia`,
  anamnesis: `${API_BASE_URL}/anamnesis`,
};