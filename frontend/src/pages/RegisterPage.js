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
        
        // Generación automática de usuario: primer_nombre.primer_apellido
        const partesNombre = formData.nombre_completo.trim().toLowerCase().split(/\s+/);
        const generadoUsername = partesNombre.length > 1 
            ? `${partesNombre[0]}.${partesNombre[1]}` 
            : partesNombre[0];

        try {
            const dataFinal = { ...formData, username: generadoUsername };
            await register(dataFinal);
            setMensaje({ 
                texto: `Registro exitoso. Su usuario generado es: ${generadoUsername}`, 
                tipo: 'success' 
            });
            setTimeout(() => onGoToLogin(), 4000);
        } catch (err) {
            setMensaje({ texto: "Error al registrar: verifique los datos o el servidor", tipo: 'error' });
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h2 style={styles.title}>Ficha de Registro</h2>
                <p style={styles.subtitle}>Información del Tutor / Especialista</p>

                <form onSubmit={handleSubmit} style={styles.grid}>
                    
                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Nombre Completo</label>
                        <input name="nombre_completo" placeholder="Ej: Pedro Pérez" onChange={handleChange} style={styles.input} required />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Correo Electrónico</label>
                        <input name="email" type="email" placeholder="correo@ejemplo.com" onChange={handleChange} style={styles.input} required />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Número de Celular</label>
                        <input name="celular" placeholder="70000000" onChange={handleChange} style={styles.input} required />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Ocupación</label>
                        <input name="ocupacion" placeholder="Ej: Ingeniero / Padre" onChange={handleChange} style={styles.input} required />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Zona de Residencia (La Paz)</label>
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
                        {mensaje.texto && (
                            <p style={{ 
                                color: mensaje.tipo === 'error' ? '#e74c3c' : '#27ae60', 
                                fontSize: '14px',
                                marginBottom: '15px'
                            }}>
                                {mensaje.texto}
                            </p>
                        )}
                        <button type="submit" style={styles.button}>Registrar y Generar Acceso</button>
                        <p style={styles.link} onClick={onGoToLogin}>¿Ya tiene cuenta? Inicie sesión</p>
                    </div>
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
        minHeight: '100vh', 
        backgroundColor: '#f4f7f6', 
        padding: '20px' 
    },
    card: { 
        padding: '40px', 
        backgroundColor: '#fff', 
        borderRadius: '12px', 
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
        width: '100%', 
        maxWidth: '650px',
        boxSizing: 'border-box'
    },
    title: { 
        textAlign: 'center', 
        margin: '0 0 8px 0', 
        color: '#2c3e50',
        fontSize: '24px'
    },
    subtitle: {
        textAlign: 'center',
        color: '#95a5a6',
        fontSize: '14px',
        marginBottom: '30px'
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
        borderRadius: '6px', 
        border: '1px solid #dcdde1', 
        fontSize: '14px',
        boxSizing: 'border-box',
        outline: 'none'
    },
    select: {
        width: '100%',
        padding: '12px', 
        borderRadius: '6px', 
        border: '1px solid #dcdde1', 
        fontSize: '14px',
        backgroundColor: '#fff',
        boxSizing: 'border-box',
        outline: 'none',
        height: '45px'
    },
    passwordWrapper: {
        position: 'relative',
        width: '100%'
    },
    inputPassword: {
        width: '100%',
        padding: '12px',
        paddingRight: '65px',
        borderRadius: '6px',
        border: '1px solid #dcdde1',
        fontSize: '14px',
        boxSizing: 'border-box',
        outline: 'none'
    },
    eyeIcon: {
        position: 'absolute',
        right: '12px',
        top: '50%',
        transform: 'translateY(-50%)',
        cursor: 'pointer',
        fontSize: '10px',
        color: '#3498db',
        fontWeight: 'bold',
        textTransform: 'uppercase',
        userSelect: 'none'
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
        borderRadius: '6px', 
        cursor: 'pointer', 
        fontWeight: '600',
        fontSize: '15px',
        transition: 'background 0.3s'
    },
    link: { 
        textAlign: 'center', 
        marginTop: '20px', 
        cursor: 'pointer', 
        color: '#3498db',
        fontSize: '13px'
    }
};

export default RegisterPage;