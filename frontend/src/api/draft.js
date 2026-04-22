// frontend/src/api/draft.js
import client from './client'; // Твой настроенный axios

export const draftApi = {
  /**
   * Настроить сессию драфта
   * @param {number} tournamentId ID турнира
   * @param {object} setupData { captain_user_ids, team_names, pick_time_seconds, team_size, role_slots }
   */
  setupDraft: (tournamentId, setupData) => {
    return client.post(`/admin/draft/${tournamentId}/setup/`, setupData).then(res => res.data);
  },

  /**
   * Запустить драфт
   * @param {number} sessionId ID сессии драфта
   */
  startDraft: (sessionId) => {
    return client.post(`/admin/draft/${sessionId}/start/`).then(res => res.data);
  },

  /**
   * Получить полное начальное состояние драфта
   * @param {number} sessionId ID сессии драфта
   */
  getState: (sessionId) => {
    return client.get(`/draft/${sessionId}`).then(res => res.data);
  },

  /**
   * Сделать пик
   * @param {number} sessionId ID сессии
   * @param {object} pickData { picked_user_id, assigned_role }
   */
  makePick: (sessionId, pickData) => {
    return client.post(`/draft/${sessionId}/pick/`, pickData).then(res => res.data);
  },

  /**
   * [АДМИН] Завершить драфт и создать команды
   * @param {number} sessionId ID сессии драфта
   */
  completeDraft: (sessionId) => {
    return client.post(`/admin/draft/${sessionId}/complete/`).then(res => res.data);
  },
};