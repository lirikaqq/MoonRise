// frontend/src/api/tournaments.js
import client from './client';

export const tournamentsApi = {
  // ==================== ПУБЛИЧНЫЕ МЕТОДЫ ====================
  getAll: async (params = {}) => {
    // Возвращаем как было
    const res = await client.get('tournaments', { params }); 
    return res.data;
  },
  
  getById: async (id) => {
    const res = await client.get(`tournaments/${id}`);
    return res.data;
  },

  // ==================== РЕГИСТРАЦИЯ ====================
  getMyStatus: async (tournamentId) => {
    const res = await client.get(`tournaments/${tournamentId}/my-status`);
    return res.data;
  },

  registerForMix: async (tournamentId, data) => {
    const res = await client.post(`tournaments/${tournamentId}/register/mix`, {
      primary_role: data.primaryRole,
      secondary_role: data.secondaryRole,
      bio: data.bio || null,
      confirmed_friend_request: data.confirmedFriendRequest, // ← добавили
      confirmed_rules: data.confirmedRules                   // ← добавили
    });
    return res.data;
  },

  registerForDraft: async (tournamentId, data) => {
    const res = await client.post(`tournaments/${tournamentId}/register/draft`, {
      primary_role: data.primaryRole,
      secondary_role: data.secondaryRole,
      bio: data.bio || null,
      rating_claimed: data.ratingClaimed,
      battletag_id: data.battletagId || null,
      new_battletag: data.newBattletag || null,
      confirmed_friend_request: data.confirmedFriendRequest,
      confirmed_rules: data.confirmedRules                   // ← добавили
    });
    return res.data;
  },
  checkin: async (tournamentId) => {
    const res = await client.post(`tournaments/${tournamentId}/checkin`);
    return res.data;
  },

  // ==================== АДМИНСКИЕ МЕТОДЫ ====================
  create: async (data) => {
    const res = await client.post('tournaments', data);
    return res.data;
  },

  update: async (id, data) => {
    const res = await client.put(`tournaments/${id}`, data);
    return res.data;
  },

  delete: async (id) => {
    const res = await client.delete(`tournaments/${id}`);
    return res.data;
  },

  updateStatus: async (id, newStatus) => {
    const res = await client.patch(`tournaments/${id}/status`, null, { params: { new_status: newStatus } });
    return res.data;
  },

  // ==================== АДМИНКА ЗАЯВОК ====================
  getApplications: async (tournamentId, statusFilter = null) => {
    const params = new URLSearchParams();
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }
    const res = await client.get(`tournaments/${tournamentId}/applications?${params.toString()}`);
    return res.data;
  },

  // НОВЫЙ МЕТОД ДЛЯ ПОЛУЧЕНИЯ ВСЕХ ЗАЯВОК ЮЗЕРА
  getMyAllApplications: async () => {
    const res = await client.get('/users/me/applications');
    return res.data;
  },

  approveApplication: async (tournamentId, userId, ratingApproved = null) => {
    const res = await client.post(`tournaments/${tournamentId}/applications/${userId}/approve`, {
      rating_approved: ratingApproved,
    });
    return res.data;
  },

  rejectApplication: async (tournamentId, userId, reason = null) => {
    const res = await client.post(`tournaments/${tournamentId}/applications/${userId}/reject`, {
      reason: reason,
    });
    return res.data;
  },

  // ==================== УЧАСТНИКИ ====================
  getParticipants: async (tournamentId) => {
    const res = await client.get(`tournaments/${tournamentId}/participants`);
    return res.data;
  },
};

export const getTournaments = () => tournamentsApi.getAll();
export default tournamentsApi;