// frontend/src/api/tournaments.js
import client from './client';

export const tournamentsApi = {
  // ==================== ПУБЛИЧНЫЕ МЕТОДЫ ====================
  getAll: async (params = {}) => {
    const res = await client.get('tournaments/', { params });
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
      confirmed_friend_request: data.confirmedFriendRequest,
      confirmed_rules: data.confirmedRules
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
      confirmed_rules: data.confirmedRules
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
    if (statusFilter) params.append('status_filter', statusFilter);
    const res = await client.get(`tournaments/${tournamentId}/applications?${params.toString()}`);
    return res.data;
  },

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

  // ==================== ДОБАВЛЕНИЕ УЧАСТНИКА ====================
  addParticipant: async (tournamentId, data) => {
    const res = await client.post(`tournaments/${tournamentId}/add-participant`, data);
    return res.data;
  },

  // ==================== ПОИСК ПОЛЬЗОВАТЕЛЕЙ ====================
  searchUsers: async (query) => {
    const res = await client.get(`tournaments/users/search?q=${encodeURIComponent(query)}`);
    return res.data;
  },

  // ==================== ПОИСК УЧАСТНИКОВ ТУРНИРА ====================
  searchTournamentPlayers: async (tournamentId, query) => {
    const res = await client.get(
      `tournaments/${tournamentId}/participants?search=${encodeURIComponent(query)}`
    );
    return res.data;
  },

  // ==================== ЗАМЕНА ИГРОКА В КОМАНДЕ ====================
  replacePlayer: async (tournamentId, teamId, oldParticipantId, newUserId) => {
    const res = await client.post(
      `tournaments/${tournamentId}/teams/${teamId}/replace/${oldParticipantId}`,
      { new_user_id: newUserId }
    );
    return res.data;
  },
  
  // ==================== УЧАСТНИКИ ====================
  getParticipants: async (tournamentId) => {
    const res = await client.get(`tournaments/${tournamentId}/participants`);
    return res.data;
  },

  // ==================== КОМАНДЫ ====================
  getTeams: async (tournamentId) => {
    const res = await client.get(`tournaments/${tournamentId}/teams`);
    return res.data;
  },

  getFreePlayers: async (tournamentId) => {
    const res = await client.get(`tournaments/${tournamentId}/free-players`);
    return res.data;
  },

  createTeam: async (tournamentId, data) => {
    const res = await client.post(`tournaments/${tournamentId}/teams`, data);
    return res.data;
  },

  // ==================== КАПИТАНЫ ====================
  promoteParticipant: async (participantId) => {
    const res = await client.post(`tournaments/participants/${participantId}/promote`);
    return res.data;
  },

  demoteParticipant: async (participantId) => {
    const res = await client.post(`tournaments/participants/${participantId}/demote`);
    return res.data;
  },
};

// Старые именованные экспорты для совместимости
export const getTournaments = () => tournamentsApi.getAll();
export const getTournamentById = (id) => tournamentsApi.getById(id);

export default tournamentsApi;