// frontend/src/pages/TournamentAdminDashboard/useTournamentAdmin.js
import { useState, useEffect, useCallback } from 'react';
import tournamentsApi from '../../api/tournaments';

export const useTournamentAdmin = (tournamentId) => {
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadTournament = useCallback(async () => {
    if (!tournamentId) return;
    
    setLoading(true);
    try {
      const data = await tournamentsApi.getById(tournamentId);
      setTournament(data);
    } catch (error) {
      console.error('Failed to load tournament:', error);
      setTournament(null);
    } finally {
      setLoading(false);
    }
  }, [tournamentId]);

  const refreshTournament = useCallback(async () => {
    setRefreshing(true);
    try {
      const data = await tournamentsApi.getById(tournamentId);
      setTournament(data);
    } catch (error) {
      console.error('Failed to refresh tournament:', error);
    } finally {
      setRefreshing(false);
    }
  }, [tournamentId]);

  // Первичная загрузка
  useEffect(() => {
    loadTournament();
  }, [loadTournament]);

  return {
    tournament,
    loading,
    refreshing,
    refreshTournament,
    setTournament, // на случай если нужно обновить вручную
  };
};