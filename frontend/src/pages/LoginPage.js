import React, { useState } from 'react';
import { login } from '../api/authService';

const LoginPage = ({ onLoginSuccess, onGoToRegister }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [rolSeleccionado, setRolSeleccionado] = useState('padres');
    const [cargando, setCargando] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setCargando(true);

        console.log("=== DATOS A ENVIAR ===");
        console.log("Username:", username);
        console.log("Password:", password);
        console.log("Rol seleccionado:", rolSeleccionado);

        if (!username || !password) {
            setError("Por favor, complete todos los campos");
            setCargando(false);
            return;
        }

        try {
            console.log("Enviando petición a:", "http://localhost:8003/auth/login");
            const data = await login(username, password);
            console.log("Respuesta recibida:", data);
            
            if (data.status === "success") {
                localStorage.setItem('user', JSON.stringify(data.usuario));
                onLoginSuccess(data.usuario);
            } else {
                setError("Credenciales incorrectas");
            }
        } catch (err) {
            console.error("ERROR COMPLETO:", err);
            console.error("Response:", err.response);
            console.error("Response data:", err.response?.data);
            setError(err.response?.data?.detail || "Error de conexión con el servidor");
        } finally {
            setCargando(false);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.background}>
                <div style={styles.cardContainer}>
                    <div style={styles.card}>
                        <div style={styles.header}>
                            <h1 style={styles.title}>Las Voces del Illimani</h1>
                            <p style={styles.subtitle}>Sistema Experto Fonoaudiológico</p>
                        </div>

                        <div style={styles.selectorRol}>
                            <button
                                onClick={() => setRolSeleccionado('padres')}
                                style={{
                                    ...styles.rolButton,
                                    ...(rolSeleccionado === 'padres' ? styles.rolButtonActive : {})
                                }}
                            >
                                Tutor / Padre
                            </button>
                            <button
                                onClick={() => setRolSeleccionado('ninos')}
                                style={{
                                    ...styles.rolButton,
                                    ...(rolSeleccionado === 'ninos' ? styles.rolButtonActive : {})
                                }}
                            >
                                Niño
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} style={styles.form}>
                            <div style={styles.inputGroup}>
                                <label style={styles.label}>Usuario</label>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    style={styles.input}
                                    placeholder={rolSeleccionado === 'ninos' ? "Ej: Mateo" : "Ej: maria.perez"}
                                    required
                                />
                            </div>

                            <div style={styles.inputGroup}>
                                <label style={styles.label}>Contraseña</label>
                                <div style={styles.passwordWrapper}>
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        style={styles.input}
                                        placeholder={rolSeleccionado === 'ninos' ? "Ej: 15/03/2019" : "••••••••"}
                                        required
                                    />
                                    <span
                                        onClick={() => setShowPassword(!showPassword)}
                                        style={styles.eyeIcon}
                                    >
                                        {showPassword ? "Ocultar" : "Mostrar"}
                                    </span>
                                </div>
                            </div>

                            {rolSeleccionado === 'ninos' && (
                                <div style={styles.ayuda}>
                                    Los niños usan su nombre como usuario y su fecha de nacimiento como contraseña
                                </div>
                            )}

                            {error && <p style={styles.errorText}>{error}</p>}

                            <button
                                type="submit"
                                style={styles.button}
                                disabled={cargando}
                            >
                                {cargando ? 'Cargando...' : 'INICIAR SESIÓN'}
                            </button>

                            {rolSeleccionado === 'padres' && (
                                <p style={styles.registerLink}>
                                    ¿No tienes cuenta?{' '}
                                    <span style={styles.linkAction} onClick={onGoToRegister}>
                                        Regístrate aquí
                                    </span>
                                </p>
                            )}
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: {
        width: '100%',
        minHeight: '100vh',
        overflow: 'hidden'
    },
    background: {
        width: '100%',
        minHeight: '100vh',
        backgroundImage: 'url("/images/fondo.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        position: 'relative',
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center'
    },
    cardContainer: {
        width: '100%',
        maxWidth: '440px',
        marginRight: '8%',
        padding: '20px'
    },
    card: {
        backgroundColor: 'rgba(255, 255, 255, 0.70)',
        borderRadius: '20px',
        padding: '35px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
        backdropFilter: 'blur(2px)'
    },
    header: {
        textAlign: 'center',
        marginBottom: '30px'
    },
    title: {
        fontSize: '26px',
        fontWeight: 'bold',
        color: '#2c3e50',
        margin: '0 0 8px 0'
    },
    subtitle: {
        fontSize: '13px',
        color: '#7f8182',
        margin: 0
    },
    selectorRol: {
        display: 'flex',
        gap: '12px',
        marginBottom: '25px',
        backgroundColor: '#f0f0f0',
        borderRadius: '40px',
        padding: '5px'
    },
    rolButton: {
        flex: 1,
        padding: '12px',
        borderRadius: '35px',
        border: 'none',
        backgroundColor: 'transparent',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: '500',
        color: '#7f8c8d',
        transition: 'all 0.2s ease'
    },
    rolButtonActive: {
        backgroundColor: '#2c3e50',
        color: 'white'
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
    },
    inputGroup: {
        textAlign: 'left'
    },
    label: {
        display: 'block',
        fontSize: '13px',
        fontWeight: '500',
        color: '#34495e',
        marginBottom: '6px'
    },
    input: {
        width: '100%',
        padding: '14px',
        borderRadius: '12px',
        border: '1px solid #e0e0e0',
        fontSize: '14px',
        outline: 'none',
        boxSizing: 'border-box',
        transition: 'border-color 0.2s'
    },
    passwordWrapper: {
        position: 'relative',
        width: '100%'
    },
    eyeIcon: {
        position: 'absolute',
        right: '14px',
        top: '50%',
        transform: 'translateY(-50%)',
        cursor: 'pointer',
        fontSize: '12px',
        color: '#3498db',
        fontWeight: '500'
    },
    ayuda: {
        fontSize: '11px',
        color: '#7f8c8d',
        backgroundColor: '#f8f9fa',
        padding: '10px',
        borderRadius: '10px',
        textAlign: 'center',
        lineHeight: '1.5'
    },
    errorText: {
        color: '#e74c3c',
        fontSize: '13px',
        margin: 0,
        textAlign: 'center'
    },
    button: {
        padding: '14px',
        backgroundColor: '#2c3e50',
        color: 'white',
        border: 'none',
        borderRadius: '40px',
        cursor: 'pointer',
        fontSize: '15px',
        fontWeight: '600',
        transition: 'background-color 0.2s'
    },
    registerLink: {
        textAlign: 'center',
        fontSize: '12px',
        color: '#6ec405',
        margin: '15px 0 0'
    },
    linkAction: {
        color: '#3498db',
        cursor: 'pointer',
        fontWeight: '500'
    }
};

export default LoginPage;