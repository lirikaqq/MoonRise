import { createContext, useContext, useState, useEffect } from 'react'
import client from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  // При загрузке — проверяем токен
  useEffect(() => {
    if (token) {
      fetchUser(token)
    } else {
      setLoading(false)
    }
  }, [token])

  async function fetchUser(jwt) {
    try {
      const response = await client.get(`/auth/me?token=${jwt}`)
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  function login() {
    // Редирект на Discord OAuth
    window.location.href = 'http://localhost:8000/auth/discord'
  }

  function logout() {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  function saveToken(newToken) {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  return (
    <AuthContext.Provider value={{ user, loading, token, login, logout, saveToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}