import client from './client'

export const playersApi = {
  getAll: async (searchQuery = '') => {
    const params = searchQuery ? { search: searchQuery } : {}
    const res = await client.get('players/', { params })
    return res.data
  },

  getById: async (id) => {
    const res = await client.get(`players/${id}/`)
    return res.data
  },

  getPlayerTournaments: async (playerId) => {
    const res = await client.get(`players/${playerId}/tournaments/`)
    return res.data
  },

  getProfileStats: async (playerId) => {
    const res = await client.get(`players/${playerId}/profile-stats/`)
    return res.data
  },

  getTopHeroes: async (playerId, limit = 5) => {
    const res = await client.get(`players/${playerId}/top-heroes/`, { params: { limit } })
    return res.data
  },

  getMatchHistory: async (playerId) => {
    const res = await client.get(`players/${playerId}/match-history/`)
    return res.data
  },

  update: async (userId, data) => {
    const res = await client.put(`players/${userId}/`, data)
    return res.data
  },

  delete: async (id) => {
    const res = await client.delete(`players/${id}/`);
    return res.data;
  },
}