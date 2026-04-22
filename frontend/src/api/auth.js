import client from './client'

export const authApi = {
  // Логин через Discord - прямой редирект (не через client, т.к. это навигация, не fetch)
  getDiscordLoginUrl: () => {
    return 'http://localhost:8000/api/auth/discord'
  },

  // Получить данные пользователя
  getMe: async (token) => {
    const response = await client.get('/auth/me', { params: { token } })
    return response.data
  },
}
