import os
import numpy as np
import librosa
import soundfile as sf # Motor portátil para WAV
import traceback
import logging
from models.conexion_db import db_admin

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MFCCService:
    def __init__(self):
        self.SR = 16000
        self.PATH_PATRONES = "data/patrones"
        
        self.MAPEO_FONEMAS = {
            'r': 1, 'rr': 2, 's': 3, 'l': 4, 'c': 5,
            't': 6, 'd': 7, 'p': 8, 'b': 9, 'g': 10,
            'f': 14, 'ch': 16, 'ere': 1,
        }
#inicio modificado por edad 26-06-2024
    def calcular_alpha_por_edad(self, edad: int) -> float:
        """
        Alpha para similitud MFCC.
        A mayor edad, MÁS ESTRICTO (alpha más bajo).
        """
        if edad < 6:
            return 15.0   # 5 años: más permisivo
        elif edad < 8:
            return 12.0    # 6-7 años: moderado
        elif edad < 10:
            return 9.0    # 8-9 años: más estricto
        else:
            return 7.0    # 10 años: muy estricto
#fin modificado por edad 26-06-2024

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
            logger.error("--- ERROR EN EXTRACCIÓN MFCC ---")
            traceback.print_exc()
            raise e

    def calcular_similitud_difusa(self, v_nino, v_patron, alpha):
        distancia = np.linalg.norm(v_patron - v_nino)
        similitud = np.exp(-distancia / alpha)
        return float(similitud)

    def procesar_evaluacion(self, audio_nino_path: str, fonema: str, id_ev: int, edad: int):
        # 1. Calcular alpha basado en edad
        alpha = self.calcular_alpha_por_edad(edad)
        logger.info(f"MFCC: Usando alpha={alpha} para edad={edad}")
        
        # 2. Cargar patrón
        patron_npy = os.path.join(self.PATH_PATRONES, f"{fonema}.npy")
        patron_wav = os.path.join(self.PATH_PATRONES, f"{fonema}.wav")
        
        v_patron = None
        
        if os.path.exists(patron_npy):
            v_patron = np.load(patron_npy)
            logger.info(f"MFCC: Patrón cargado de {patron_npy}")
        elif os.path.exists(patron_wav):
            v_patron = self.extraer_vector_mfcc(patron_wav)
            logger.info(f"MFCC: Patrón extraído de {patron_wav}")
        else:
            logger.error(f"MFCC: CRÍTICO - No existe patrón para [{fonema}]")
            return 0.0

        # 3. Extraer vector del niño
        try:
            v_nino = self.extraer_vector_mfcc(audio_nino_path)
            logger.info(f"MFCC: Vector del niño extraído correctamente")
        except Exception as e:
            logger.error(f"MFCC: Error extrayendo vector del niño: {e}")
            return 0.0
        
        # 4. Calcular similitud
        distancia = np.linalg.norm(v_patron - v_nino)
        similitud = np.exp(-distancia / alpha)
        logger.info(f"MFCC: distancia={distancia:.4f}, alpha={alpha}, similitud={similitud:.4f}")
        
        # 5. Guardar en BD (solo si id_ev es válido)
        if id_ev > 0:
            try:
                with db_admin.obtener_conexion() as conn:
                    cursor = conn.cursor()
                    query = """
                        INSERT INTO memoria_trabajo (id_ev, id_hecho, valor_obtenido, confiabilidad, fuente)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE valor_obtenido = VALUES(valor_obtenido)
                    """
                    cursor.execute(query, (id_ev, id_hecho, similitud, 0.85, "MFCC"))
                    conn.commit()
                    logger.info(f"MFCC: Guardado en BD - id_hecho={id_hecho}, similitud={similitud:.4f}")
            except Exception as e:
                logger.error(f"MFCC: Error guardando en BD: {e}")
        
        return similitud