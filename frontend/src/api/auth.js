import axios from 'axios'

// Через Vite proxy - все запросы через /api
const API_URL = '/api'

export const authApi = {
  // Логин через Discord - прямой редирект
  getDiscordLoginUrl: () => {
    return 'http://localhost:8000/auth/discord'
  },

  // Получить данные пользователя через proxy
  getMe: async (token) => {
    const response = await axios.get(`${API_URL}/auth/me`, {
      params: { token }
    })
    return response.data
  },
}