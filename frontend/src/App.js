import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TutorDashboard from './pages/TutorDashboard';
import NinoDashboard from './pages/NinoDashboard';
import JuegosDashboard from './pages/JuegosDashboard';
import ProgresoPage from './pages/ProgresoPage';
import EvaluacionPage from './pages/EvaluacionPage';

function App() {
  const [user, setUser] = useState(null);
  const [vistaActual, setVistaActual] = useState('login'); // 'login', 'registro', 'progreso', 'evaluacion'
  const [ninoProgreso, setNinoProgreso] = useState(null);
  const [evaluacionNino, setEvaluacionNino] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('user');
      }
    }
  }, []);

  // Función para abrir la página de progreso
  const verProgreso = (nino) => {
    setNinoProgreso(nino);
    setVistaActual('progreso');
  };

  // Función para iniciar evaluación
  const iniciarEvaluacionNino = (nino) => {
    setEvaluacionNino(nino);
    setVistaActual('evaluacion');
  };

  // Función para volver al dashboard
  const volverAlDashboard = () => {
    setNinoProgreso(null);
    setEvaluacionNino(null);
    setVistaActual('dashboard');
  };

  if (!user) {
    return (
      vistaActual === 'login' 
        ? <LoginPage 
            onLoginSuccess={(u) => setUser(u)} 
            onGoToRegister={() => setVistaActual('registro')} 
          />
        : <RegisterPage onGoToLogin={() => setVistaActual('login')} />
    );
  }

  // Redirigir según el rol
  if (user.id_rol === 3 || user.rol === 'nino') {
    if (vistaActual === 'juegos') {
      return (
        <JuegosDashboard
          idNino={user.id_nino}
          onBack={() => setVistaActual('dashboard')}
        />
      );
    }

    return (
      <NinoDashboard 
        usuario={user} 
        onLogout={() => {
          localStorage.removeItem('user');
          setUser(null);
        }}
        onVerJuegos={() => setVistaActual('juegos')}
      />
    );
  }

  // Vista de progreso
  if (vistaActual === 'progreso' && ninoProgreso) {
    return (
      <ProgresoPage 
        idNino={ninoProgreso.id_nino} 
        nombreNino={ninoProgreso.nombre}
        onBack={volverAlDashboard}
      />
    );
  }

  // Vista de evaluación
  if (vistaActual === 'evaluacion' && evaluacionNino) {
    return (
      <EvaluacionPage 
        idNino={evaluacionNino.id_nino} 
        onBack={volverAlDashboard} 
      />
    );
  }

  // Vista del dashboard del tutor
  return (
    <TutorDashboard 
      usuario={user} 
      onLogout={() => {
        localStorage.removeItem('user');
        setUser(null);
      }} 
      onVerProgreso={verProgreso}
      onIniciarEvaluacion={iniciarEvaluacionNino}
    />
  );
}

export default App;