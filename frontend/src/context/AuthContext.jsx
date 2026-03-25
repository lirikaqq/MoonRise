import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // При загрузке — проверяем токен
  useEffect(() => {
    const token = localStorage.getItem('moonrise_token')
    if (token) {
      authApi.getMe(token)
        .then(data => setUser(data))
        .catch(() => {
          localStorage.removeItem('moonrise_token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = (token, userData) => {
    localStorage.setItem('moonrise_token', token)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('moonrise_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}