// frontend/src/pages/AuthCallback.jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthCallback() {
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');

    console.log('🔑 Token from URL:', token ? '✅ получен' : '❌ null');

    const handleAuth = async () => {
      if (token) {
        await login(token);  // ✅ ждём — user установится ДО navigate
        navigate('/', { replace: true });
      } else {
        console.error('❌ No token in callback URL');
        navigate('/');
      }
    };

    handleAuth();
  }, []); // eslint-disable-line

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      color: 'white',
      fontSize: '1.2rem'
    }}>
      Авторизация...
    </div>
  );
}