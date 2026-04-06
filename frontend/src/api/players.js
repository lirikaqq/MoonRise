import client from './client'

export const playersApi = {
  getAll: async (searchQuery = '') => {
    const params = searchQuery ? { search: searchQuery } : {}
    // СЛЭШ УБРАН
    const res = await client.get('players', { params }) 
    return res.data
  },
  
  getById: async (id) => {
    // СЛЭШ УБРАН
    const res = await client.get(`players/${id}`)
    return res.data
  },

  getPlayerTournaments: async (playerId) => {
    // СЛЭШ УБРАН
    const res = await client.get(`players/${playerId}/tournaments`)
    return res.data
  },

  update: async (userId, data) => {
    // СЛЭШ УБРАН
    const res = await client.put(`players/${userId}`, data)
    return res.data
  },

  delete: async (id) => {
    // СЛЭШ УБРАН
    const res = await client.delete(`players/${id}`);
    return res.data;
  },
}