// frontend/src/pages/TournamentAdminDashboard/TournamentAdminHeader.jsx
import { RefreshCw, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const statusConfig = {
  upcoming: { label: 'Предстоящий', color: 'bg-gray-500' },
  registration: { label: 'Регистрация', color: 'bg-blue-500' },
  checkin: { label: 'Check-in', color: 'bg-purple-500' },
  draft: { label: 'Драфт', color: 'bg-amber-500' },
  ongoing: { label: 'В процессе', color: 'bg-emerald-500' },
  completed: { label: 'Завершён', color: 'bg-zinc-400' },
  cancelled: { label: 'Отменён', color: 'bg-red-500' },
};

const formatConfig = {
  draft: { label: 'DRAFT', color: 'text-violet-400' },
  mix: { label: 'MIX', color: 'text-cyan-400' },
};

const TournamentAdminHeader = ({ tournament, onRefresh, refreshing }) => {
  const navigate = useNavigate();

  const statusInfo = statusConfig[tournament.status] || { label: tournament.status, color: 'bg-gray-500' };
  const formatInfo = formatConfig[tournament.format] || { label: tournament.format.toUpperCase(), color: 'text-gray-400' };

  const renderTeamConfig = () => {
    if (!tournament.team_config) return null;

    const { team_size, roles } = tournament.team_config;
    const roleEntries = Object.entries(roles || {});

    return (
      <div className="admin-team-config">
        <span className="admin-config-label">{team_size}v{team_size}</span>
        <div className="admin-roles">
          {roleEntries.map(([role, count]) => (
            <span key={role} className="admin-role-badge">
              {role.toUpperCase()}<span className="role-count">{count}</span>
            </span>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="admin-header">
      <div className="admin-header-top">
        <button 
          className="admin-back-btn"
          onClick={() => navigate(`/tournaments/${tournament.id}`)}
        >
          <ArrowLeft size={20} />
          На страницу турнира
        </button>

        <button 
          className="admin-refresh-btn"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
          Обновить
        </button>
      </div>

      <div className="admin-tournament-title">
        <h1>{tournament.title}</h1>
        {tournament.division && (
          <span className="admin-division-badge">Division {tournament.division}</span>
        )}
      </div>

      <div className="admin-tournament-meta">
        <div className="admin-meta-badges">
          <span className={`admin-badge admin-badge-format ${formatInfo.color}`}>
            {formatInfo.label}
          </span>
          
          <span className={`admin-badge admin-badge-status ${statusInfo.color}`}>
            {statusInfo.label}
          </span>

          {tournament.structure_type && (
            <span className="admin-badge admin-badge-structure">
              {tournament.structure_type.replace('_', ' ')}
            </span>
          )}
        </div>

        {renderTeamConfig()}

        {tournament.description && (
          <p className="admin-tournament-description">
            {tournament.description}
          </p>
        )}
      </div>

      {/* Статистика */}
      <div className="admin-stats-row">
        <div className="admin-stat">
          <div className="stat-value">
            {tournament.participant_count || 0}
          </div>
          <div className="stat-label">Заявки</div>
        </div>
        <div className="admin-stat">
          <div className="stat-value">
            {tournament.team_count || 0}
          </div>
          <div className="stat-label">Команды</div>
        </div>
        <div className="admin-stat">
          <div className="stat-value">
            {tournament.encounter_count || 0}
          </div>
          <div className="stat-label">Матчи</div>
        </div>
      </div>
    </div>
  );
};

export default TournamentAdminHeader;