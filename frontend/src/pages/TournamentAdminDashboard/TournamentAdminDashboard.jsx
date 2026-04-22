// frontend/src/pages/TournamentAdminDashboard/TournamentAdminDashboard.jsx
import { useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

import { useTournamentAdmin } from './useTournamentAdmin';
import TournamentAdminHeader from './TournamentAdminHeader';
import TabNavigation from './components/TabNavigation';

import ApplicationsTab from './tabs/ApplicationsTab';
import TeamsTab from './tabs/TeamsTab';
import BracketTab from './tabs/BracketTab';
import ManagementTab from './tabs/ManagementTab';
import DevToolsTab from './tabs/DevToolsTab';

import './TournamentAdminDashboard.css';

const TABS = [
  { key: 'applications', label: 'ЗАЯВКИ', icon: '📋' },
  { key: 'teams', label: 'КОМАНДЫ', icon: '👥' },
  { key: 'bracket', label: 'СЕТКА', icon: '🏆' },
  { key: 'management', label: 'УПРАВЛЕНИЕ', icon: '⚙️' },
];

const TournamentAdminDashboard = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  const activeTab = searchParams.get('tab') || 'applications';
  const tournamentId = Number(id);

  const {
    tournament,
    loading,
    refreshing,
    refreshTournament,
  } = useTournamentAdmin(tournamentId);

  // Защита маршрута
  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/');
    }
  }, [user, navigate]);

  const handleTabChange = (tabKey) => {
    setSearchParams({ tab: tabKey });
  };

  if (loading) return <div className="admin-loading">Загрузка турнира...</div>;
  if (!tournament) return <div className="admin-empty">Турнир не найден</div>;

  return (
    <div className="tournament-admin-dashboard">
      <TournamentAdminHeader
        tournament={tournament}
        onRefresh={refreshTournament}
        refreshing={refreshing}
      />

      <TabNavigation
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      <div className="admin-content">
        {activeTab === 'applications' && (
          <ApplicationsTab
            tournamentId={tournamentId}
            tournament={tournament}
            onRefresh={refreshTournament}
          />
        )}

        {activeTab === 'teams' && (
          <TeamsTab
            tournamentId={tournamentId}
            tournament={tournament}
            onRefresh={refreshTournament}
          />
        )}

        {activeTab === 'bracket' && (
          <BracketTab
            tournamentId={tournamentId}
            tournament={tournament}
            onRefresh={refreshTournament}
          />
        )}

        {activeTab === 'management' && (
          <ManagementTab
            tournamentId={tournamentId}
            tournament={tournament}
            onRefresh={refreshTournament}
          />
        )}

        {activeTab === 'dev' && import.meta.env.DEV && (
          <DevToolsTab
            tournamentId={tournamentId}
            tournament={tournament}
            onRefresh={refreshTournament}
          />
        )}
      </div>
    </div>
  );
};

export default TournamentAdminDashboard;