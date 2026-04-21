import React, { useState } from 'react';
import { login } from '../api/authService';

const LoginPage = ({ onLoginSuccess, onGoToRegister }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!username || !password) {
            setError("Por favor, complete todos los campos");
            return;
        }

        try {
            const data = await login(username, password);
            if (data.status === "success") {
                localStorage.setItem('user', JSON.stringify(data.usuario));
                onLoginSuccess(data.usuario);
            } else {
                setError("Credenciales incorrectas");
            }
        } catch (err) {
            setError("Error de conexión con el servidor");
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h2 style={styles.title}>FonoApp Expert</h2>
                <p style={styles.subtitle}>Sistema Experto de Apoyo Fonoaudiológico</p>

                <form onSubmit={handleSubmit}>
                    {/* USUARIO */}
                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Nombre de Usuario</label>
                        <input 
                            type="text" 
                            value={username} 
                            onChange={(e) => setUsername(e.target.value)} 
                            style={styles.input}
                            placeholder="Ej: Pedro Perez"
                            required
                        />
                    </div>

                    {/* CONTRASEÑA */}
                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Contraseña</label>
                        <div style={styles.passwordWrapper}>
                            <input 
                                type={showPassword ? "text" : "password"}
                                value={password} 
                                onChange={(e) => setPassword(e.target.value)} 
                                style={styles.inputPassword}
                                placeholder="••••••••"
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

                    {error && <p style={styles.errorText}>{error}</p>}

                    <button type="submit" style={styles.button}>
                        Iniciar Sesión
                    </button>

                    <p style={styles.registerLink} onClick={onGoToRegister}>
                        ¿No tiene una cuenta? <span style={styles.linkAction}>Regístrese aquí</span>
                    </p>
                </form>
            </div>
        </div>
    );
};

const styles = {
    container: {
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f4f7f6' // Fondo neutro profesional
    },
    card: {
        padding: '40px',
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
        width: '380px',
        textAlign: 'center',
        boxSizing: 'border-box'
    },
    title: {
        color: '#2c3e50',
        fontSize: '24px',
        margin: '0 0 8px 0',
        fontWeight: '600'
    },
    subtitle: {
        color: '#95a5a6',
        marginBottom: '30px',
        fontSize: '14px'
    },
    inputGroup: {
        marginBottom: '20px',
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
        padding: '12px',
        borderRadius: '6px',
        border: '1px solid #dcdde1',
        outline: 'none',
        fontSize: '14px',
        boxSizing: 'border-box', // Clave para que midan lo mismo
        transition: 'border-color 0.3s'
    },
    passwordWrapper: {
        position: 'relative',
        width: '100%',
        boxSizing: 'border-box'
    },
    inputPassword: {
        width: '100%',
        padding: '12px',
        paddingRight: '65px',
        borderRadius: '6px',
        border: '1px solid #dcdde1',
        outline: 'none',
        fontSize: '14px',
        boxSizing: 'border-box'
    },
    eyeIcon: {
        position: 'absolute',
        right: '12px',
        top: '50%',
        transform: 'translateY(-50%)',
        cursor: 'pointer',
        fontSize: '11px',
        color: '#3498db',
        fontWeight: 'bold',
        textTransform: 'uppercase',
        userSelect: 'none'
    },
    button: {
        width: '100%',
        padding: '12px',
        backgroundColor: '#2c3e50', // Color institucional serio
        color: '#fff',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        fontSize: '15px',
        fontWeight: '600',
        marginTop: '10px',
        transition: 'background-color 0.3s'
    },
    registerLink: {
        marginTop: '25px',
        fontSize: '13px',
        color: '#7f8c8d'
    },
    linkAction: {
        color: '#3498db',
        cursor: 'pointer',
        fontWeight: '500'
    },
    errorText: {
        color: '#e74c3c',
        fontSize: '13px',
        marginBottom: '15px',
        fontWeight: '500'
    }
};

export default LoginPage;