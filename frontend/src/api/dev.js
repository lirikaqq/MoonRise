import client from './client'

/**
 * [DEV ONLY] Создать фиктивных участников для турнира.
 * Доступен только в development окружении.
 */
export const seedParticipants = async (tournamentId) => {
  const res = await client.post(`/dev/tournaments/${tournamentId}/seed-participants`)
  return res.data
}

/**
 * [DEV ONLY] Сбросить драфт турнира.
 * Доступен только в development окружении.
 */
export const resetDraft = async (tournamentId) => {
  const res = await client.post(`/dev/tournaments/${tournamentId}/reset-draft`)
  return res.data
}

/**
 * [DEV ONLY] Удалить всех участников турнира.
 * Доступен только в development окружении.
 */
export const deleteAllParticipants = async (tournamentId) => {
  const res = await client.delete(`/dev/tournaments/${tournamentId}/participants`)
  return res.data
}
