import os
import numpy as np
import librosa
import soundfile as sf # Motor portátil para WAV
import traceback
from models.conexion_db import db_admin

class MFCCService:
    def __init__(self):
        self.ALPHA = 7.5 
        self.SR = 16000
        self.PATH_PATRONES = "data/patrones"
        
        self.MAPEO_FONEMAS = {
            'r': 1, 'rr': 2, 's': 3, 'l': 4, 'c': 5,
            't': 6, 'd': 7, 'p': 8, 'b': 9, 'g': 10,
            'f': 14, 'ch': 16, 'ere': 1,
        }

    def extraer_vector_mfcc(self, path: str):
        try:
            # CARGA PORTÁTIL: Leemos con soundfile para archivos WAV
            data, native_sr = sf.read(path)
            
            # Convertir a mono si es estéreo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Re-muestreo a 16000Hz si es necesario
            if native_sr != self.SR:
                y = librosa.resample(data, orig_sr=native_sr, target_sr=self.SR)
            else:
                y = data

            if len(y) == 0:
                raise ValueError("Archivo de audio vacío")

            # Pre-énfasis (Ec. 2.9 de la tesis)
            y = np.append(y[0], y[1:] - 0.97 * y[:-1]) 
            
            # Extracción de 13 coeficientes
            mfccs = librosa.feature.mfcc(y=y, sr=self.SR, n_mfcc=13)
            return np.mean(mfccs, axis=1)
        except Exception as e:
            print(f"--- ERROR EN EXTRACCIÓN MFCC ---")
            traceback.print_exc()
            raise e

    def calcular_similitud_difusa(self, v_nino, v_patron):
        distancia = np.linalg.norm(v_patron - v_nino)
        similitud = np.exp(-distancia / self.ALPHA)
        return float(similitud)
#puedes que aqui este el error pot id_ev
    def procesar_evaluacion(self, audio_nino_path: str, fonema: str, id_ev: int):
        patron_path = os.path.join(self.PATH_PATRONES, f"{fonema}.npy")
        
        if not os.path.exists(patron_path):
            print(f"Error: Patrón no encontrado en {patron_path}")
            return 0.0

        v_patron = np.load(patron_path)
        v_nino = self.extraer_vector_mfcc(audio_nino_path)
        
        fc_obtenido = self.calcular_similitud_difusa(v_nino, v_patron)
        id_hecho = self.MAPEO_FONEMAS.get(fonema, 0)

        if id_hecho > 0:
            with db_admin.obtener_conexion() as conn:
                cursor = conn.cursor()
                query = """
                    INSERT INTO memoria_trabajo (id_ev, id_hecho, valor_obtenido) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE valor_obtenido = %s
                """
                cursor.execute(query, (id_ev, id_hecho, fc_obtenido, fc_obtenido))
                conn.commit()
        
        return fc_obtenido