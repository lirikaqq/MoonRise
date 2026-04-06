// frontend/src/api/draft.js
import client from './client'; // Твой настроенный axios

export const draftApi = {
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
    return client.post(`/draft/${sessionId}/pick`, pickData).then(res => res.data);
  },
};