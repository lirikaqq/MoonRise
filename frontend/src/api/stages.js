import client from './client';

/**
 * API клиент для управления этапами турнира.
 */

// === STAGES ===

export const createStage = async (stageData) => {
  const response = await client.post('/stages/', stageData);
  return response.data;
};

export const getTournamentStages = async (tournamentId) => {
  const response = await client.get(`/stages/tournament/${tournamentId}`);
  return response.data;
};

export const getStage = async (stageId) => {
  const response = await client.get(`/stages/${stageId}`);
  return response.data;
};

export const updateStage = async (stageId, stageData) => {
  const response = await client.put(`/stages/${stageId}`, stageData);
  return response.data;
};

export const deleteStage = async (stageId) => {
  const response = await client.delete(`/stages/${stageId}`);
  return response.data;
};

export const generateStageMatches = async (stageId) => {
  const response = await client.post(`/stages/${stageId}/generate-matches`);
  return response.data;
};

export const advanceToNextStage = async (stageId) => {
  const response = await client.post(`/stages/${stageId}/advance`);
  return response.data;
};

// === GROUPS ===

export const createGroup = async (stageId, groupData) => {
  const response = await client.post(`/stages/${stageId}/groups`, groupData);
  return response.data;
};

export const getStageGroups = async (stageId) => {
  const response = await client.get(`/stages/${stageId}/groups`);
  return response.data;
};

export const updateGroup = async (groupId, groupData) => {
  const response = await client.put(`/stages/groups/${groupId}`, groupData);
  return response.data;
};

export const deleteGroup = async (groupId) => {
  const response = await client.delete(`/stages/groups/${groupId}`);
  return response.data;
};

// === PARTICIPANTS ===

export const assignParticipantToGroup = async (groupId, participantId, seed = null) => {
  const response = await client.post(
    `/stages/groups/${groupId}/participants/${participantId}`,
    null,
    { params: { seed } }
  );
  return response.data;
};

export const bulkAssignParticipants = async (groupId, participantIds, startSeed = 1) => {
  const response = await client.post(
    `/stages/groups/${groupId}/participants/bulk`,
    participantIds,
    { params: { start_seed: startSeed } }
  );
  return response.data;
};
