// frontend/src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import client from '../api/client'; // Убедись, что client настроен правильно

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // useCallback, чтобы функция не пересоздавалась на каждый рендер
  const fetchMe = useCallback(async () => {
    // Получаем токен ПЕРЕД запросом
    const token = localStorage.getItem('moonrise_token');
    if (!token) {
        setUser(null);
        setLoading(false);
        return;
    }
    
    // Временно добавляем токен в заголовок для этого запроса
    // (Лучше делать это через interceptors в client.js)
    try {
      const response = await client.get('/users/me', { // <-- ПРЕДПОЛАГАЮ, ЧТО ПУТЬ /users/me
          headers: {
              'Authorization': `Bearer ${token}`
          }
      });
      console.log('✅ fetchMe success:', response.data);
      setUser(response.data);
    } catch (error) {
      console.error('❌ fetchMe failed:', error.response?.status, error.response?.data);
      localStorage.removeItem('moonrise_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Этот useEffect запускается один раз при старте приложения
  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = async (token) => {
    console.log('🔐 login() called');
    localStorage.setItem('moonrise_token', token);
    // После логина сразу запрашиваем данные пользователя
    await fetchMe();
  };

  const logout = () => {
    localStorage.removeItem('moonrise_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);