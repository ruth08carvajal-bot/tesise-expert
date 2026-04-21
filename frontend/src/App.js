import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TutorDashboard from './pages/TutorDashboard';

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

  return (
    <TutorDashboard usuario={user} onLogout={() => {
      localStorage.removeItem('user');
      setUser(null);
    }} />
  );
}

export default App;