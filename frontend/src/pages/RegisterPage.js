import React, { useState } from 'react';
import { register } from '../api/authService';

const RegisterPage = ({ onGoToLogin }) => {
    const [formData, setFormData] = useState({
        nombre_completo: '',
        email: '',
        celular: '',
        ocupacion: '',
        zona: 'Sopocachi',
        password: ''
    });

    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [showPassword, setShowPassword] = useState(false);

    const zonasPaceñas = [
        "Sopocachi", "Miraflores", "Zona Sur", "Centro", 
        "Villa Fátima", "Max Paredes", "Cotahuma", "San Antonio"
    ];

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const partesNombre = formData.nombre_completo.trim().toLowerCase().split(/\s+/);
        const generadoUsername = partesNombre.length > 1 
            ? `${partesNombre[0]}.${partesNombre[1]}` 
            : partesNombre[0];

        try {
            const dataFinal = { ...formData, username: generadoUsername };
            await register(dataFinal);
            setMensaje({ 
                texto: `✅ Registro exitoso. Su usuario generado es: ${generadoUsername}`, 
                tipo: 'success' 
            });
            setTimeout(() => onGoToLogin(), 4000);
        } catch (err) {
            setMensaje({ texto: "❌ Error al registrar: verifique los datos o el servidor", tipo: 'error' });
        }
    };

    return (
        <div style={styles.container}>
            {/* Fondo de imagen */}
            <div style={styles.backgroundImage} />
            
            {/* Contenido */}
            <div style={styles.content}>
                <div style={styles.card}>
                    <h2 style={styles.title}> Ficha de Registro</h2>
                    <p style={styles.subtitle}>Información del Tutor / Especialista</p>

                    {mensaje.texto && (
                        <div style={{
                            ...styles.mensaje,
                            backgroundColor: mensaje.tipo === 'error' ? '#f8d7da' : '#d4edda',
                            color: mensaje.tipo === 'error' ? '#721c24' : '#155724'
                        }}>
                            {mensaje.texto}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} style={styles.grid}>
                        <div style={styles.inputGroup}>
                            <label style={styles.label}> Nombre Completo</label>
                            <input name="nombre_completo" placeholder="Ej: Pedro Pérez" onChange={handleChange} style={styles.input} required />
                        </div>

                        <div style={styles.inputGroup}>
                            <label style={styles.label}> Correo Electrónico</label>
                            <input name="email" type="email" placeholder="correo@ejemplo.com" onChange={handleChange} style={styles.input} required />
                        </div>

                        <div style={styles.inputGroup}>
                            <label style={styles.label}>Número de Celular</label>
                            <input name="celular" placeholder="70000000" onChange={handleChange} style={styles.input} required />
                        </div>

                        <div style={styles.inputGroup}>
                            <label style={styles.label}> Ocupación</label>
                            <input name="ocupacion" placeholder="Ej: Ingeniero / Padre" onChange={handleChange} style={styles.input} required />
                        </div>

                        <div style={styles.inputGroup}>
                            <label style={styles.label}>Zona de Residencia</label>
                            <select name="zona" onChange={handleChange} style={styles.select}>
                                {zonasPaceñas.map(z => <option key={z} value={z}>{z}</option>)}
                            </select>
                        </div>

                        <div style={styles.inputGroup}>
                            <label style={styles.label}>Contraseña</label>
                            <div style={styles.passwordWrapper}>
                                <input 
                                    name="password"
                                    type={showPassword ? "text" : "password"} 
                                    placeholder="••••••••" 
                                    onChange={handleChange} 
                                    style={styles.inputPassword} 
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

                        <div style={styles.footer}>
                            <button type="submit" style={styles.button}>
                                Registrarse
                            </button>
                            <p style={styles.link} onClick={onGoToLogin}>
                                ¿Ya tienes cuenta? <span style={styles.linkAction}>Inicia sesión</span>
                            </p>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: {
        position: 'relative',
        minHeight: '100vh',
        overflow: 'hidden'
    },
    backgroundImage: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'url("/images/fondo_registro.png")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        zIndex: 0
    },
    content: {
        position: 'relative',
        zIndex: 1,
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px'
    },
    card: { 
        backgroundColor: 'rgba(255, 255, 255, 0.59)',
        borderRadius: '20px',
        padding: '40px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
        width: '100%', 
        maxWidth: '700px',
        backdropFilter: 'blur(5px)'
    },
    title: { 
        textAlign: 'center', 
        margin: '0 0 8px 0', 
        color: '#2c3e50',
        fontSize: '26px',
        fontWeight: 'bold'
    },
    subtitle: {
        textAlign: 'center',
        color: '#404141',
        fontSize: '14px',
        marginBottom: '30px'
    },
    mensaje: {
        padding: '12px',
        borderRadius: '10px',
        marginBottom: '20px',
        textAlign: 'center',
        fontSize: '14px'
    },
    grid: { 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
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
        padding: '12px', 
        borderRadius: '10px', 
        border: '1px solid #ddd', 
        fontSize: '14px',
        boxSizing: 'border-box',
        outline: 'none',
        transition: 'border-color 0.2s'
    },
    select: {
        width: '100%',
        padding: '12px', 
        borderRadius: '10px', 
        border: '1px solid #ddd', 
        fontSize: '14px',
        backgroundColor: '#fff',
        boxSizing: 'border-box',
        outline: 'none',
        height: '46px'
    },
    passwordWrapper: {
        position: 'relative',
        width: '100%'
    },
    inputPassword: {
        width: '100%',
        padding: '12px',
        paddingRight: '70px',
        borderRadius: '10px',
        border: '1px solid #ddd',
        fontSize: '14px',
        boxSizing: 'border-box',
        outline: 'none'
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
    footer: { 
        gridColumn: '1 / span 2', 
        textAlign: 'center',
        marginTop: '10px'
    },
    button: { 
        width: '100%', 
        padding: '14px', 
        backgroundColor: '#2c3e50', 
        color: 'white', 
        border: 'none', 
        borderRadius: '30px', 
        cursor: 'pointer', 
        fontWeight: '600',
        fontSize: '16px',
        transition: 'background 0.3s'
    },
    link: { 
        textAlign: 'center', 
        marginTop: '20px', 
        fontSize: '15px',
        color: '#464a4a'
    },
    linkAction: { 
        color: '#3498db',
        cursor: 'pointer',
        fontWeight: '500'
    }
};

export default RegisterPage;