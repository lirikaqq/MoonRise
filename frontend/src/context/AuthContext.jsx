// frontend/src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const abortControllerRef = useRef(null);

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem('moonrise_token');
    if (!token) {
        console.debug('[AuthContext] No token found, setting guest mode');
        setUser(null);
        setLoading(false);
        return;
    }

    // Отменяем предыдущий запрос если он ещё pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    console.debug('[AuthContext] Fetching /users/me...');
    try {
      const response = await client.get('/users/me', {
          headers: {
              'Authorization': `Bearer ${token}`
          },
          signal: abortControllerRef.signal,
      });
      console.debug('[AuthContext] /users/me success:', response.data);
      setUser(response.data);
    } catch (error) {
      if (error.name === 'AbortError') {
        console.debug('[AuthContext] /users/me request aborted');
        return;
      }
      if (error.code === 'ECONNABORTED') {
        console.error('⏱️ [AuthContext] /users/me timeout (10s)');
      } else if (error.code === 'ERR_NETWORK') {
        console.error('🌐 [AuthContext] /users/me network error — backend unreachable');
      } else {
        console.error('❌ [AuthContext] /users/me failed:', error.response?.status, error.response?.data?.detail);
      }
      localStorage.removeItem('moonrise_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Этот useEffect запускается один раз при старте приложения
  useEffect(() => {
    fetchMe();

    // Cleanup: отменяем запрос при размонтировании
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchMe]);

  const login = async (token) => {
    console.log('🔐 login() called');
    localStorage.setItem('moonrise_token', token);
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