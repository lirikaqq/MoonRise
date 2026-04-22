import client from './client'

// ==================== TEAMS ====================

export const getTeamsByTournament = async (tournamentId) => {
  const res = await client.get(`matches/teams/tournament/${tournamentId}/`)
  return res.data
}

export const createTeam = async (data) => {
  const res = await client.post('/matches/teams/', data)
  return res.data
}

// ==================== ENCOUNTERS ====================

export const getEncountersByTournament = async (tournamentId) => {
  const res = await client.get(`matches/encounters/tournament/${tournamentId}/`)
  return res.data
}

export const getEncounterById = async (encounterId) => {
  const res = await client.get(`matches/encounters/${encounterId}/`)
  return res.data
}

export const createEncounter = async (data) => {
  const res = await client.post('matches/encounters/', data)
  return res.data
}

// ==================== LOG UPLOAD ====================

export const uploadMatchLog = async ({
  file,
  encounterId,
  mapNumber,
  playerMappings = [],
}) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('encounter_id', encounterId)
  if (mapNumber) formData.append('map_number', mapNumber)
  if (playerMappings.length > 0) {
    formData.append('player_mappings', JSON.stringify(playerMappings))
  }

  // Content-Type НЕ ставим — браузер сам добавит boundary для FormData
 const res = await client.post('matches/upload/', formData)
  return res.data
}

// ==================== MATCH HISTORY ====================

export const getPlayerMatchHistory = async (userId) => {
  const res = await client.get(`matches/player/${userId}/history/`)
  return res.data
}

export const getMatchById = async (matchId) => {
  const res = await client.get(`matches/${matchId}/`)
  return res.data
}

export const getMatchKillFeed = async (matchId) => {
  const res = await client.get(`matches/${matchId}/killfeed/`)
  return res.data
}

export const deleteMatch = async (matchId) => {
  const res = await client.delete(`matches/${matchId}/`)
  return res.data
}

export const getMatchFirstBlood = async (matchId) => {
  const res = await client.get(`matches/${matchId}/first-blood/`)
  return res.data
}

// ==================== ADMIN: ENCOUNTER RESULT ====================

export const reportEncounterResult = async (encounterId, team1Score, team2Score) => {
  const res = await client.put(`matches/admin/encounters/${encounterId}/report-result`, {
    team1_score: team1Score,
    team2_score: team2Score,
  })
  return res.data
}

