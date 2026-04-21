import librosa
import numpy as np
import os

def procesar_mis_grabaciones():
    # Rutas
    ruta_wavs = "data/referencias/"
    ruta_salida = "data/patrones/"
    
    if not os.path.exists(ruta_salida):
        os.makedirs(ruta_salida)

    # Lista de tus 13 fonemas (nombres de archivo sin el _perfecto.wav)
    archivos = [f for f in os.listdir(ruta_wavs) if f.endswith('.wav')]

    print(f"--- Iniciando procesamiento de {len(archivos)} audios ---")

    for nombre_archivo in archivos:
        path_completo = os.path.join(ruta_wavs, nombre_archivo)
        
        try:
            # 1. Carga del audio (Standard 16kHz)
            y, sr = librosa.load(path_completo, sr=16000)
            
            # 2. Pre-énfasis (Para resaltar frecuencias de fonemas)
            y_filt = np.append(y[0], y[1:] - 0.97 * y[:-1])
            
            # 3. Extracción de MFCC (Ecuación 2.10 de tu tesis)
            # Extraemos 13 coeficientes
            mfcc_feat = librosa.feature.mfcc(y=y_filt, sr=sr, n_mfcc=13)
            
            # 4. Promedio temporal (Vector de 13 dimensiones)
            # Esto es lo que compararemos contra el niño
            vector_maestro = np.mean(mfcc_feat, axis=1)
            
            # 5. Guardar el patrón matemático
            # r_perfecto.wav -> r.npy
            nombre_limpio = nombre_archivo.replace("_perfecto.wav", "")
            np.save(os.path.join(ruta_salida, f"{nombre_limpio}.npy"), vector_maestro)
            
            print(f"✅ Patrón '{nombre_limpio}' generado correctamente.")
            
        except Exception as e:
            print(f"❌ Error procesando {nombre_archivo}: {e}")

if __name__ == "__main__":
    procesar_mis_grabaciones()