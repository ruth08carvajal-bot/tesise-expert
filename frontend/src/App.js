import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TutorDashboard from './pages/TutorDashboard';
import NinoDashboard from './pages/NinoDashboard';

function App() {
  const [user, setUser] = useState(null);
  const [vistaActual, setVistaActual] = useState('login'); // 'login' o 'registro'

  useEffect(() => {
    // Verificar si hay un usuario guardado en localStorage
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
  // inicio Redirigir según el rol 26/04/2026
  if (user.id_rol === 3 || user.rol === 'nino') {
    return (
      <NinoDashboard 
        usuario={user} 
        onLogout={() => {
          localStorage.removeItem('user');
          setUser(null);
        }} 
      />
    );
  }
  // fin Redirigir según el rol 26/04/2026

  return (
    <TutorDashboard usuario={user} onLogout={() => {
      localStorage.removeItem('user');
      setUser(null);
    }} />
  );
}

export default App;