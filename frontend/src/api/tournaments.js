import axios from 'axios'

const API_URL = '/api'

export const tournamentsApi = {
  getAll: async ({ format = null, search = null, skip = 0, limit = 20 } = {}) => {
    const params = {}
    if (format && format !== 'all') params.format = format
    if (search) params.search = search
    params.skip = skip
    params.limit = limit
    const response = await axios.get(`${API_URL}/tournaments`, { params })
    return response.data
  },

  getById: async (id) => {
    const response = await axios.get(`${API_URL}/tournaments/${id}`)
    return response.data
  },

  register: async (id, token) => {
    const response = await axios.post(
      `${API_URL}/tournaments/${id}/register`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    )
    return response.data
  },

  checkin: async (id, token) => {
    const response = await axios.post(
      `${API_URL}/tournaments/${id}/checkin`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    )
    return response.data
  },
}