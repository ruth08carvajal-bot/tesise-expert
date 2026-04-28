import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PracticaEjercicio from '../components/Ejercicio/PracticaEjercicio';

const API_URL = 'http://127.0.0.1:8003/ejercicios';

const NinoDashboard = ({ usuario, onLogout }) => {
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [ejercicioSeleccionado, setEjercicioSeleccionado] = useState(null);
    const [feedback, setFeedback] = useState({ texto: '', tipo: '', mostrar: false });
    const [nivelActual, setNivelActual] = useState(1);
    const [nombreNivel, setNombreNivel] = useState('Bajo');
    const [progresoNivel, setProgresoNivel] = useState(0);
    const [estrellasTotales, setEstrellasTotales] = useState(0);
    const [mostrarCelebracion, setMostrarCelebracion] = useState(false);
    const [nivelDesbloqueado, setNivelDesbloqueado] = useState(null);
    const [ejerciciosPorNivel, setEjerciciosPorNivel] = useState({});
    const [imagenPerfil, setImagenPerfil] = useState(null);

    const nivelesConfig = [
        { id: 1, nombre: "🌱 Nivel 1", titulo: "Sonidos Básicos", icono: "🎤", color: "#27ae60", ejerciciosEsperados: 3 },
        { id: 2, nombre: "⭐ Nivel 2", titulo: "Praxias Linguales", icono: "👅", color: "#3498db", ejerciciosEsperados: 3 },
        { id: 3, nombre: "🏆 Nivel 3", titulo: "Soplo Controlado", icono: "💨", color: "#f39c12", ejerciciosEsperados: 3 },
        { id: 4, nombre: "🚀 Nivel 4", titulo: "Ritmo y Fluidez", icono: "🎵", color: "#9b59b6", ejerciciosEsperados: 3 },
        { id: 5, nombre: "👑 Nivel 5", titulo: "Maestro del Habla", icono: "🏆", color: "#e74c3c", ejerciciosEsperados: 3 }
    ];

    useEffect(() => {
        const cargarDatos = async () => {
            try {
                const response = await axios.get(`${API_URL}/mis-ejercicios/${usuario.id_nino}`);
                if (response.data.status === 'success') {
                    const ejerciciosRaw = response.data.ejercicios;
                    
                    const porNivel = {
                        'Bajo': [],
                        'Medio': [],
                        'Alto': []
                    };
                    
                    ejerciciosRaw.forEach(ej => {
                        const nivel = ej.nivel || 'Bajo';
                        porNivel[nivel].push(ej);
                    });
                    
                    setEjerciciosPorNivel(porNivel);
                    
                    let nivelMaximo = 1;
                    let nivelActualNombre = 'Bajo';
                    
                    const ejerciciosBajo = porNivel['Bajo'];
                    const completadosBajo = ejerciciosBajo.filter(e => e.rendimiento_previo >= 0.7).length;
                    const totalBajo = ejerciciosBajo.length;
                    const progresoBajo = totalBajo > 0 ? (completadosBajo / totalBajo) * 100 : 0;
                    
                    if (progresoBajo >= 70) {
                        nivelMaximo = 2;
                        nivelActualNombre = 'Medio';
                        
                        const ejerciciosMedio = porNivel['Medio'];
                        const completadosMedio = ejerciciosMedio.filter(e => e.rendimiento_previo >= 0.7).length;
                        const totalMedio = ejerciciosMedio.length;
                        const progresoMedio = totalMedio > 0 ? (completadosMedio / totalMedio) * 100 : 0;
                        
                        if (progresoMedio >= 70) {
                            nivelMaximo = 3;
                            nivelActualNombre = 'Alto';
                        }
                    }
                    
                    setNivelActual(nivelMaximo);
                    setNombreNivel(nivelActualNombre);
                    
                    const estrellas = ejerciciosRaw.reduce((sum, ej) => {
                        if (ej.rendimiento_previo >= 0.9) return sum + 3;
                        if (ej.rendimiento_previo >= 0.7) return sum + 2;
                        if (ej.rendimiento_previo >= 0.5) return sum + 1;
                        return sum;
                    }, 0);
                    setEstrellasTotales(estrellas);
                    
                    const ejerciciosNivelActual = porNivel[nivelActualNombre] || [];
                    const completadosActual = ejerciciosNivelActual.filter(e => e.rendimiento_previo >= 0.7).length;
                    const totalActual = ejerciciosNivelActual.length;
                    const progreso = totalActual > 0 ? (completadosActual / totalActual) * 100 : 0;
                    setProgresoNivel(progreso);
                }
                
                if (usuario.genero === 'niño') {
                    setImagenPerfil('/images/nino_default.png');
                } else if (usuario.genero === 'niña') {
                    setImagenPerfil('/images/niña_default.png');
                } else {
                    setImagenPerfil('/images/avatar_default.png');
                }
                
            } catch (err) {
                console.error('Error cargando datos:', err);
                setError('No se pudieron cargar tus ejercicios');
            } finally {
                setCargando(false);
            }
        };

        if (usuario.id_nino) {
            cargarDatos();
        }
    }, [usuario.id_nino, usuario.genero]);

    const handlePracticar = (ejercicio) => {
        setEjercicioSeleccionado(ejercicio);
    };

    const handleVolver = () => {
        setEjercicioSeleccionado(null);
        window.location.reload();
    };

    const handleGuardarProgreso = async (idEjercicio, puntaje, tiempo) => {
        try {
            const response = await axios.post(`${API_URL}/guardar-progreso`, {
                id_nino: usuario.id_nino,
                id_ejercicio: idEjercicio,
                puntaje_obtenido: puntaje,
                tiempo_empleado: tiempo
            });
            
            if (response.data.status === 'success') {
                let estrellasGanadas = 0;
                let mensajeExtra = '';
                let efecto = '';
                
                if (puntaje >= 0.9) {
                    estrellasGanadas = 3;
                    mensajeExtra = '🎉 ¡Perfecto! 3 estrellas';
                    efecto = '✨✨✨';
                } else if (puntaje >= 0.7) {
                    estrellasGanadas = 2;
                    mensajeExtra = '⭐ ¡Muy bien! 2 estrellas';
                    efecto = '✨✨';
                } else if (puntaje >= 0.5) {
                    estrellasGanadas = 1;
                    mensajeExtra = '🌟 ¡Bien hecho! 1 estrella';
                    efecto = '✨';
                } else {
                    mensajeExtra = '💪 ¡Sigue practicando! Cada intento cuenta';
                }
                
                setFeedback({ 
                    texto: `${efecto} ${Math.round(puntaje * 100)}% - ${mensajeExtra}`, 
                    tipo: 'success', 
                    mostrar: true 
                });
                
                setEstrellasTotales(prev => prev + estrellasGanadas);
                
                const progresoAnterior = progresoNivel;
                const nuevoProgreso = progresoAnterior + (100 / ejerciciosNivelActual.length);
                
                if (progresoAnterior < 70 && nuevoProgreso >= 70) {
                    setMostrarCelebracion(true);
                    setNivelDesbloqueado(nivelActual + 1);
                    setTimeout(() => {
                        setMostrarCelebracion(false);
                        window.location.reload();
                    }, 3000);
                }
                
                setTimeout(() => setFeedback({ texto: '', tipo: '', mostrar: false }), 3000);
            }
        } catch (err) {
            console.error('Error guardando progreso:', err);
            setFeedback({ texto: '😅 Hubo un error, intenta de nuevo', tipo: 'error', mostrar: true });
            setTimeout(() => setFeedback({ texto: '', tipo: '', mostrar: false }), 3000);
        }
    };

    const ejerciciosNivelActual = ejerciciosPorNivel[nombreNivel] || [];

    if (cargando) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.loadingContainer}>
                    <div style={styles.spinner}></div>
                    <p>🎮 Cargando tu aventura...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.container}>
                <div style={styles.backgroundImage} />
                <div style={styles.errorContainer}>
                    <div style={styles.errorIcon}>😢</div>
                    <p>{error}</p>
                    <button onClick={onLogout} style={styles.backButton}>Salir</button>
                </div>
            </div>
        );
    }

    if (ejercicioSeleccionado) {
        return (
            <PracticaEjercicio 
                ejercicio={ejercicioSeleccionado}
                idNino={usuario.id_nino}
                onGuardarProgreso={handleGuardarProgreso}
                onVolver={handleVolver}
            />
        );
    }

    const nivelInfo = nivelesConfig[nivelActual - 1] || nivelesConfig[0];
    
    return (
        <div style={styles.container}>
            <div style={styles.backgroundImage} />
            
            {mostrarCelebracion && (
                <div style={styles.celebracionOverlay}>
                    <div style={styles.celebracionContent}>
                        <div style={styles.celebracionIcon}>🎉</div>
                        <h2 style={styles.celebracionTitle}>¡NIVEL COMPLETADO!</h2>
                        <p style={styles.celebracionText}>
                          Has desbloqueado el nivel {nivelDesbloqueado}
                        </p>
                        <div style={styles.confetti}>🎊 ✨ 🎉 ✨ 🎊</div>
                    </div>
                </div>
            )}
            
            <div style={styles.content}>
                {/* Cabecera - Avatar grande en esquina superior izquierda */}
                <div style={styles.header}>
                    <div style={styles.avatarContainer}>
                        {imagenPerfil ? (
                            <img src={imagenPerfil} alt="avatar" style={styles.avatarImagen} />
                        ) : (
                            <div style={styles.avatarEmoji}>
                                {usuario.genero === 'niño' ? '👦' : usuario.genero === 'niña' ? '👧' : '🎮'}
                            </div>
                        )}
                        <label style={styles.cambiarImagenBtn}>
                            📷
                            <input 
                                type="file" 
                                accept="image/*" 
                                style={{ display: 'none' }}
                                onChange={(e) => {
                                    if (e.target.files[0]) {
                                        const url = URL.createObjectURL(e.target.files[0]);
                                        setImagenPerfil(url);
                                    }
                                }}
                            />
                        </label>
                    </div>
                    
                    <div style={styles.userInfo}>
                        <h1 style={styles.greeting}>¡Hola, {usuario.nombre}! 👋</h1>
                        <p style={styles.subGreeting}>Aventura del Habla</p>
                    </div>
                    
                    <div style={styles.starsContainer}>
                        <span style={styles.starsIcon}>⭐</span>
                        <span style={styles.starsCount}>{estrellasTotales}</span>
                    </div>
                    
                    <button onClick={onLogout} style={styles.logoutButton}>
                        🚪 Salir
                    </button>
                </div>

                {/* Nivel actual */}
                <div style={styles.nivelCard}>
                    <div style={styles.nivelHeader}>
                        <div style={styles.nivelIcon}>{nivelInfo.icono}</div>
                        <div>
                            <h2 style={styles.nivelTitle}>{nivelInfo.nombre}</h2>
                            <p style={styles.nivelSubtitle}>{nivelInfo.titulo}</p>
                        </div>
                        <div style={styles.nivelProgress}>
                            <div style={styles.progressBarContainer}>
                                <div style={{ ...styles.progressBarFill, width: `${progresoNivel}%` }} />
                            </div>
                            <span>{Math.round(progresoNivel)}%</span>
                        </div>
                    </div>
                </div>

                {/* ========== SENDERO AL ILLIMANI (CORREGIDO: ARRIBA LA CUMBRE, ABAJO EL INICIO) ========== */}
                <div style={styles.senderoContainer}>
                    <h2 style={styles.senderoTitulo}>
                        <span style={styles.senderoIcon}>🏔️</span> 
                        Subiendo al Illimani 
                        <span style={styles.senderoIcon}>🗻</span>
                    </h2>
                    
                    {ejerciciosNivelActual.length === 0 ? (
                        <div style={styles.emptyEjercicios}>
                            <p>🎁 No hay ejercicios en este nivel aún</p>
                            <p>¡Completa el nivel anterior para desbloquear más!</p>
                        </div>
                    ) : (
                        <div style={styles.sendero}>
                            {/* CUMBRE (ARRIBA) */}
                            <div style={styles.metaCamino}>
                                <span style={styles.metaIcon}>🗻</span>
                                <span style={styles.metaTexto}>Cumbre del Illimani</span>
                                {progresoNivel >= 70 && <span style={styles.cumbreLogro}>🏆</span>}
                            </div>
                            
                            {/* Ejercicios - ordenados de la CUMBRE hacia el INICIO (visualmente de arriba a abajo) */}
                            {[...ejerciciosNivelActual].reverse().map((ej, idx) => {
                                const indiceOriginal = ejerciciosNivelActual.length - 1 - idx;
                                const rendimiento = ej.rendimiento_previo * 100;
                                const estrellas = rendimiento >= 90 ? 3 : rendimiento >= 70 ? 2 : rendimiento >= 50 ? 1 : 0;
                                const completado = rendimiento >= 70;
                                
                                let colorCirculo = '#a0a0a0';
                                if (rendimiento >= 90) colorCirculo = '#ffd700';
                                else if (rendimiento >= 70) colorCirculo = '#4caf50';
                                else if (rendimiento >= 50) colorCirculo = '#2196f3';
                                else if (rendimiento > 0) colorCirculo = '#ff9800';
                                
                                // Serpenteante: izquierda/derecha alternando
                                const esIzquierda = idx % 2 === 0;
                                const offset = esIzquierda ? -60 : 60;
                                
                                return (
                                    <div key={ej.id_ejercicio} className="sendero-paso" style={{
                                        ...styles.senderoPaso,
                                        transform: `translateX(${offset}px)`
                                    }}>
                                        {/* Línea conectora diagonal */}
                                        {idx > 0 && (
                                            <div style={{
                                                ...styles.senderoLineaDiagonal,
                                                left: esIzquierda ? 'calc(50% + 40px)' : 'calc(50% - 80px)',
                                                transform: esIzquierda ? 'rotate(25deg)' : 'rotate(-25deg)'
                                            }} />
                                        )}
                                        
                                        {/* Círculo del ejercicio */}
                                        <div 
                                            style={{
                                                ...styles.circuloSendero,
                                                backgroundColor: colorCirculo,
                                                boxShadow: completado ? '0 0 20px rgba(76,175,80,0.6)' : '0 4px 8px rgba(0,0,0,0.2)',
                                                border: completado ? '3px solid #ffd700' : '2px solid #fff'
                                            }}
                                            onClick={() => handlePracticar(ej)}
                                        >
                                            {completado && <div style={styles.senderoCheck}>✓</div>}
                                            <div style={styles.circuloSenderoIcono}>
                                                {ej.tipo_apoyo === 'MFCC' ? '🎤' : ej.tipo_apoyo === 'Selección' ? '🖱️' : '🎮'}
                                            </div>
                                            <div style={styles.circuloSenderoNumero}>{indiceOriginal + 1}</div>
                                            
                                            <div style={styles.progresoCircular}>
                                                <svg width="80" height="80" viewBox="0 0 80 80">
                                                    <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="4"/>
                                                    <circle 
                                                        cx="40" cy="40" r="34" 
                                                        fill="none" 
                                                        stroke={completado ? '#ffd700' : '#fff'} 
                                                        strokeWidth="4" 
                                                        strokeDasharray={`${(rendimiento / 100) * 213.6} 213.6`}
                                                        strokeLinecap="round"
                                                        transform="rotate(-90 40 40)"
                                                        style={{ transition: 'stroke-dasharray 0.5s ease' }}
                                                    />
                                                </svg>
                                            </div>
                                        </div>
                                        
                                        <div style={styles.senderoInfo}>
                                            <div style={styles.senderoNombre}>{ej.nombre}</div>
                                            <div style={styles.senderoEstrellas}>
                                                {Array(3).fill(0).map((_, i) => (
                                                    <span key={i} style={{ 
                                                        color: i < estrellas ? '#ffd700' : '#ddd', 
                                                        fontSize: '14px',
                                                        margin: '0 2px'
                                                    }}>★</span>
                                                ))}
                                            </div>
                                            <div style={styles.senderoPorcentaje}>
                                                {Math.round(rendimiento)}%
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            
                            {/* INICIO DEL CAMINO (ABAJO) */}
                            <div style={styles.inicioCamino}>
                                <span style={styles.inicioIcon}>🏁</span>
                                <span style={styles.inicioTexto}>Inicio del sendero</span>
                            </div>
                        </div>
                    )}
                    
                    {progresoNivel >= 70 && nivelActual < 5 && (
                        <div style={styles.cumbreMensaje}>
                            <div style={styles.cumbreIcono}>🏔️✨</div>
                            <div style={styles.cumbreTexto}>
                                ¡Llegaste a la cumbre! Siguiente nivel → {nivelActual + 1}
                            </div>
                        </div>
                    )}
                </div>

                {feedback.mostrar && (
                    <div style={styles.feedbackBubble}>
                        {feedback.texto}
                    </div>
                )}

                <div style={styles.recompensaCard}>
                    <div style={styles.recompensaIcon}>🎁</div>
                    <div style={styles.recompensaInfo}>
                        <h3 style={styles.recompensaTitle}>Recompensa diaria</h3>
                        <p style={styles.recompensaText}>¡Practica todos los días para ganar estrellas extra!</p>
                    </div>
                    <div style={styles.recompensaEstrellas}>
                        <span>⭐</span>
                        <span>+{Math.min(5, Math.floor(estrellasTotales / 10))}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: { position: 'relative', minHeight: '100vh', overflow: 'hidden' },
    backgroundImage: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'url("/images/fondo_sendero.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        zIndex: 0
    },
    content: { position: 'relative', zIndex: 1, maxWidth: '800px', margin: '0 auto', padding: '20px', minHeight: '100vh' },
    
    celebracionOverlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        animation: 'fadeIn 0.5s ease'
    },
    celebracionContent: {
        backgroundColor: 'white',
        borderRadius: '30px',
        padding: '40px',
        textAlign: 'center',
        animation: 'bounce 0.5s ease'
    },
    celebracionIcon: { fontSize: '60px', marginBottom: '20px' },
    celebracionTitle: { fontSize: '28px', color: '#f39c12', marginBottom: '10px' },
    celebracionText: { fontSize: '16px', color: '#2c3e50' },
    confetti: { fontSize: '24px', marginTop: '20px' },
    
    header: { 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        gap: '15px',
        marginBottom: '25px', 
        backgroundColor: 'rgba(255,255,255,0.9)', 
        padding: '15px 20px', 
        borderRadius: '20px',
        flexWrap: 'wrap'
    },
    avatarContainer: { 
        position: 'relative',
        width: '70px',
        height: '70px'
    },
    avatarImagen: { 
        width: '70px', 
        height: '70px', 
        borderRadius: '50%', 
        objectFit: 'cover', 
        border: '3px solid #f39c12',
        backgroundColor: '#fff'
    },
    avatarEmoji: { 
        fontSize: '60px',
        width: '70px',
        height: '70px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
    },
    cambiarImagenBtn: {
        position: 'absolute',
        bottom: '0',
        right: '0',
        backgroundColor: '#3498db',
        borderRadius: '50%',
        width: '26px',
        height: '26px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        fontSize: '12px',
        border: '2px solid white',
        color: 'white'
    },
    userInfo: { flex: 1 },
    greeting: { fontSize: '18px', color: '#2c3e50', margin: 0 },
    subGreeting: { fontSize: '12px', color: '#7f8c8d', margin: '5px 0 0' },
    starsContainer: { 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        backgroundColor: '#fff3cd', 
        padding: '8px 16px', 
        borderRadius: '25px',
        minWidth: '70px',
        justifyContent: 'center'
    },
    starsIcon: { fontSize: '20px' },
    starsCount: { fontSize: '18px', fontWeight: 'bold', color: '#f39c12' },
    logoutButton: { 
        backgroundColor: '#e74c3c', 
        color: 'white', 
        border: 'none', 
        padding: '10px 20px', 
        borderRadius: '25px', 
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        transition: 'transform 0.2s ease, background-color 0.2s ease'
    },
    
    nivelCard: { backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: '20px', padding: '20px', marginBottom: '25px' },
    nivelHeader: { display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px', flexWrap: 'wrap' },
    nivelIcon: { fontSize: '40px' },
    nivelTitle: { margin: 0, fontSize: '20px', color: '#2c3e50' },
    nivelSubtitle: { margin: '5px 0 0', fontSize: '12px', color: '#7f8c8d' },
    nivelProgress: { marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '10px' },
    progressBarContainer: { width: '100px', height: '8px', backgroundColor: '#e0e0e0', borderRadius: '10px', overflow: 'hidden' },
    progressBarFill: { height: '100%', backgroundColor: '#27ae60', borderRadius: '10px', transition: 'width 0.5s ease' },
    
    senderoContainer: {
        backgroundColor: 'rgba(76, 175, 80, 0.15)',
        borderRadius: '60px 60px 30px 30px',
        padding: '30px 20px',
        marginBottom: '25px',
        position: 'relative',
        backgroundImage: 'radial-gradient(circle at 10% 20%, rgba(139, 69, 19, 0.1) 2%, transparent 2.5%)',
        backgroundSize: '25px 25px',
        border: '1px solid rgba(139, 69, 19, 0.3)'
    },
    senderoTitulo: {
        textAlign: 'center',
        fontSize: '22px',
        color: '#5d3a1a',
        marginBottom: '40px',
        fontFamily: 'cursive',
        textShadow: '2px 2px 4px rgba(0,0,0,0.1)'
    },
    senderoIcon: { fontSize: '28px', margin: '0 15px' },
    sendero: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '20px 0'
    },
    inicioCamino: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginTop: '30px',
        padding: '10px',
        backgroundColor: 'rgba(255,255,255,0.8)',
        borderRadius: '30px',
        width: '100px'
    },
    inicioIcon: { fontSize: '30px' },
    inicioTexto: { fontSize: '10px', color: '#5d3a1a', marginTop: '5px' },
    
    senderoPaso: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: '50px',
        zIndex: 2,
        transition: 'transform 0.3s ease'
    },
    senderoLineaDiagonal: {
        position: 'absolute',
        top: '-45px',
        width: '90px',
        height: '70px',
        borderLeft: '3px dashed #8B4513',
        borderBottom: '3px dashed #8B4513',
        borderRadius: '0 0 0 35px',
        opacity: 0.6
    },
    circuloSendero: {
        width: '80px',
        height: '80px',
        borderRadius: '50%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        zIndex: 3,
        transition: 'transform 0.3s ease, box-shadow 0.3s ease',
        cursor: 'pointer',
        background: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 100%)'
    },
    circuloSenderoIcono: { fontSize: '32px', marginBottom: '4px' },
    circuloSenderoNumero: {
        fontSize: '11px',
        fontWeight: 'bold',
        color: 'white',
        backgroundColor: 'rgba(0,0,0,0.4)',
        borderRadius: '12px',
        padding: '2px 8px'
    },
    progresoCircular: {
        position: 'absolute',
        top: '-5px',
        left: '-5px',
        right: '-5px',
        bottom: '-5px',
        pointerEvents: 'none'
    },
    senderoCheck: {
        position: 'absolute',
        top: '-8px',
        right: '-8px',
        backgroundColor: '#4caf50',
        color: 'white',
        borderRadius: '50%',
        width: '24px',
        height: '24px',
        fontSize: '14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '2px solid #ffd700',
        zIndex: 4
    },
    senderoInfo: {
        textAlign: 'center',
        marginTop: '12px',
        backgroundColor: 'rgba(255,255,255,0.85)',
        padding: '8px 12px',
        borderRadius: '20px',
        minWidth: '100px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    },
    senderoNombre: {
        fontSize: '12px',
        fontWeight: 'bold',
        color: '#5d3a1a',
        maxWidth: '120px',
        wordBreak: 'break-word'
    },
    senderoEstrellas: { marginTop: '4px' },
    senderoPorcentaje: {
        fontSize: '10px',
        color: '#4caf50',
        fontWeight: 'bold',
        marginTop: '2px'
    },
    metaCamino: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: '30px',
        padding: '15px',
        backgroundColor: 'rgba(255,215,0,0.8)',
        borderRadius: '40px',
        width: '120px'
    },
    metaIcon: { fontSize: '40px' },
    metaTexto: { fontSize: '11px', fontWeight: 'bold', color: '#5d3a1a', marginTop: '5px' },
    cumbreLogro: { fontSize: '16px', marginTop: '5px' },
    
    cumbreMensaje: {
        marginTop: '30px',
        padding: '15px',
        backgroundColor: 'rgba(255, 215, 0, 0.9)',
        borderRadius: '50px',
        textAlign: 'center',
        animation: 'pulse 1.5s infinite'
    },
    cumbreIcono: { fontSize: '30px', marginBottom: '8px' },
    cumbreTexto: { fontSize: '14px', fontWeight: 'bold', color: '#5d3a1a' },
    
    recompensaCard: { display: 'flex', alignItems: 'center', gap: '15px', backgroundColor: 'rgba(255,215,0,0.9)', borderRadius: '20px', padding: '15px' },
    recompensaIcon: { fontSize: '40px' },
    recompensaInfo: { flex: 1 },
    recompensaTitle: { margin: 0, fontSize: '14px', color: '#2c3e50' },
    recompensaText: { margin: '5px 0 0', fontSize: '11px', color: '#7f8c8d' },
    recompensaEstrellas: { fontSize: '20px', fontWeight: 'bold', color: '#f39c12' },
    
    feedbackBubble: {
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: '#27ae60',
        color: 'white',
        padding: '12px 24px',
        borderRadius: '30px',
        fontSize: '14px',
        fontWeight: 'bold',
        zIndex: 100,
        animation: 'fadeInUp 0.3s ease'
    },
    
    loadingContainer: { textAlign: 'center', padding: '50px', backgroundColor: 'rgba(255,255,255,0.9)', borderRadius: '20px' },
    spinner: { border: '4px solid #f3f3f3', borderTop: '4px solid #3498db', borderRadius: '50%', width: '50px', height: '50px', animation: 'spin 1s linear infinite', margin: '0 auto 20px' },
    errorContainer: { textAlign: 'center', padding: '40px', backgroundColor: 'rgba(255,255,255,0.9)', borderRadius: '20px' },
    errorIcon: { fontSize: '48px', marginBottom: '20px' },
    backButton: { marginTop: '20px', backgroundColor: '#6c757d', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer' },
    emptyEjercicios: { textAlign: 'center', padding: '40px', color: '#7f8c8d' }
};

const styleSheet = document.createElement("style");
styleSheet.textContent = `
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes bounce { 0% { transform: scale(0.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
    @keyframes fadeInUp { from { opacity: 0; transform: translateX(-50%) translateY(20px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
    
    .sendero-paso:hover > div:first-child {
        transform: scale(1.08);
    }
    button:hover {
        transform: scale(1.02);
    }
`;
document.head.appendChild(styleSheet);

export default NinoDashboard;