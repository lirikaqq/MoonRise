// frontend/src/pages/TournamentAdminDashboard/DashboardTabs/BracketTab.jsx
import { useState, useEffect, useCallback } from 'react';
import client from '../../../api/client';
import InteractiveBracket from '../../../components/bracket/InteractiveBracket';
import MatchModal from "../modals/MatchModal";
import '../styles/BracketTab.css';

const BracketTab = ({ tournamentId, tournament, onRefresh }) => {
  const [encounters, setEncounters] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEncounter, setSelectedEncounter] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [encData, teamsData] = await Promise.all([
        client.get(`/matches/encounters/tournament/${tournamentId}/`).then(r => r.data),
        client.get(`/matches/teams/tournament/${tournamentId}/`).then(r => r.data),
      ]);
      setEncounters(Array.isArray(encData) ? encData : []);
      setTeams(Array.isArray(teamsData) ? teamsData : []);
    } catch (err) {
      console.error('Failed to load bracket data:', err);
    } finally {
      setLoading(false);
    }
  }, [tournamentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleMatchClick = (encounter) => {
    setSelectedEncounter(encounter);
  };

  const handleModalClose = () => {
    setSelectedEncounter(null);
  };

  const isSwissOrRR = ['SWISS', 'ROUND_ROBIN', 'GROUPS_PLUS_PLAYOFF'].includes(tournament.structure_type);

  return (
    <div className="bracket-tab">
      <InteractiveBracket
        tournamentId={tournamentId}
        structureType={tournament.structure_type}
        teams={teams}
        encounters={encounters}
        onMatchClick={handleMatchClick}
        onSeedingComplete={loadData}
        onEncounterUpdated={loadData}
      />

      {isSwissOrRR && encounters.length > 0 && (
        <div className="swiss-controls">
          <button
            className="btn-swiss-next"
            onClick={async () => {
              await client.post(`/matches/admin/tournaments/${tournamentId}/swiss-next-round/`, { avoid_repeat: true });
              loadData();
            }}
          >
            🔄 Сгенерировать следующий тур
          </button>
        </div>
      )}

      {selectedEncounter && (
        <MatchModal
          encounter={selectedEncounter}
          teams={teams}
          onClose={handleModalClose}
          onUpdate={loadData}
        />
      )}

      {loading && <div className="admin-loading">Загрузка сетки...</div>}
    </div>
  );
};

export default BracketTab;