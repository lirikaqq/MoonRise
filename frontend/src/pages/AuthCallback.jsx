import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../api/auth'

export default function AuthCallback() {
  const [searchParams] = useSearchParams()
  const { login } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const token = searchParams.get('token')

    if (!token) {
      navigate('/')
      return
    }

    // Получаем данные пользователя по токену
    authApi.getMe(token)
      .then(userData => {
        login(token, userData)
        navigate('/')
      })
      .catch(() => {
        navigate('/')
      })
  }, [])

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#13242d',
      color: '#13c8b0',
      fontFamily: 'Palui, sans-serif',
      fontSize: '24px',
      letterSpacing: '0.05em',
    }}>
      АВТОРИЗАЦИЯ...
    </div>
  )
}