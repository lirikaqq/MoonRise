import { useState, useEffect, useCallback } from 'react';
import tournamentsApi from '../../../api/tournaments';
import { Plus, Users, Zap, RefreshCw, RotateCcw } from 'lucide-react';
import ReplacePlayerModal from '../modals/ReplacePlayerModal';
import '../styles/TeamsTab.css';

const TeamsTab = ({ tournamentId, tournament }) => {
  const [teams, setTeams] = useState([]);
  const [freePlayers, setFreePlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [isReplaceModalOpen, setIsReplaceModalOpen] = useState(false);
  const [playerToReplace, setPlayerToReplace] = useState(null);

  const [replacements, setReplacements] = useState({});

  const isMix = tournament?.format === 'mix';
  const teamSize = tournament?.team_config?.team_size || 5;
  const maxTeams = tournament?.team_config?.team_count || 8;

  const loadData = useCallback(async () => {
    if (!tournamentId) return;
    
    setLoading(true);
    try {
      const [teamsRes, freeRes] = await Promise.all([
        tournamentsApi.getTeams(tournamentId),
        tournamentsApi.getFreePlayers(tournamentId)
      ]);

      setTeams(teamsRes.teams || []);
      setFreePlayers(freeRes.free_players || []);
    } catch (err) {
      console.error('Ошибка загрузки данных для TeamsTab:', err);
    } finally {
      setLoading(false);
    }
  }, [tournamentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openReplaceModal = (playerId, playerName, teamId) => {
    setPlayerToReplace({ playerId, playerName, teamId });
    setIsReplaceModalOpen(true);
  };

  const normalizePlayer = (player) => {
    return {
      display_name: player.display_name || player.user_display_name || player.username || 'Неизвестный',
      username: player.username || player.user_username || '',
      application_data: player.application_data || {},
      ...player
    };
  };

  const handleReplaceSuccess = (newPlayerRaw, option) => {
    if (!playerToReplace) return;

    const newPlayer = normalizePlayer(newPlayerRaw);

    setReplacements(prev => ({
      ...prev,
      [playerToReplace.playerId]: {
        ...newPlayer,
        replacedByOption: option
      }
    }));

    setIsReplaceModalOpen(false);
    setPlayerToReplace(null);
    loadData();
  };

  const undoReplacement = (originalPlayerId) => {
    if (window.confirm('Откатить замену этого игрока?')) {
      setReplacements(prev => {
        const updated = { ...prev };
        delete updated[originalPlayerId];
        return updated;
      });
    }
  };

  const createTeamManually = async () => {
    const name = prompt('Название новой команды:');
    if (!name?.trim()) return;

    setCreating(true);
    try {
      await tournamentsApi.createTeam(tournamentId, { name: name.trim() });
      await loadData();
    } catch (err) {
      alert('Не удалось создать команду');
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const runBalancer = () => {
    if (!isMix) {
      alert('Балансер доступен только для микс-турниров');
      return;
    }
    alert('Балансер запущен.\n\nЛогика будет добавлена позже.');
  };

  if (loading) return <div className="admin-skeleton">Загрузка состава команд...</div>;

  return (
    <div className="teams-tab">
      <div className="teams-header">
        <div>
          <h2>Состав команд</h2>
          <p className="teams-subtitle">
            {isMix 
              ? `${teamSize} на ${teamSize} — команды создаются вручную или через балансер` 
              : 'Драфт-турнир — команды формируются после драфта'}
          </p>
        </div>

        <div className="teams-actions">
          {isMix && (
            <button className="btn btn-primary" onClick={createTeamManually} disabled={creating}>
              <Plus size={18} />
              Создать команду
            </button>
          )}

          <button className="btn btn-balancer" onClick={runBalancer}>
            <Zap size={18} />
            Запустить балансер
          </button>

          <button className="btn btn-small" onClick={loadData}>
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      <div className="section teams-section">
        <h3>Команды ({teams.length} из {maxTeams})</h3>
        {teams.length === 0 ? (
          <div className="empty-box">Команд пока нет</div>
        ) : (
          <div className="teams-grid">
            {teams.map(team => {
              const players = team.players || [];
              const totalRank = players.reduce((sum, p) => {
                const rank = parseInt(p.application_data?.rank || 0);
                return sum + rank;
              }, 0);
              const avgScore = players.length > 0 ? Math.round(totalRank / players.length) : 0;

              return (
                <div key={team.id} className="team-card">
                  <div className="team-header">
                    <h4>{team.name}</h4>
                    <div className="team-division">
                      Division <span className="division-number">{team.division || '—'}</span>
                    </div>
                  </div>

                  <div className="team-players">
                    {players.map(p => {
                      const app = p.application_data || {};
                      const isReplaced = !!replacements[p.id];
                      const replacement = replacements[p.id];

                      return (
                        <div key={p.id}>
                          <div 
                            className={`team-player ${isReplaced ? 'replaced' : ''}`}
                            onClick={() => openReplaceModal(p.id, p.display_name || p.username, team.id)}
                          >
                            <div className="player-main">
                              {p.display_name || p.username}
                              {p.is_captain && <span className="captain-badge">👑</span>}
                            </div>
                            <div className="player-stats">
                              <span>Div {app.division || '—'}</span>
                              <span>Rank {app.rank || '—'}</span>
                            </div>
                          </div>

                          {isReplaced && replacement && (
                            <div className="replacement-row">
                              <div className="replacement-label">Заменён на:</div>
                              <div className="team-player new-player">
                                <div className="player-main">
                                  {replacement.display_name || replacement.username || 'Неизвестно'}
                                </div>
                                <button 
                                  className="btn-undo"
                                  onClick={(e) => { e.stopPropagation(); undoReplacement(p.id); }}
                                >
                                  <RotateCcw size={16} /> Откатить
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <div className="team-footer">
                    <div className="avg-score">
                      AVG Score <span className="score-value">{avgScore}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <ReplacePlayerModal
        tournamentId={tournamentId}
        playerToReplace={playerToReplace}
        isOpen={isReplaceModalOpen}
        onClose={() => {
          setIsReplaceModalOpen(false);
          setPlayerToReplace(null);
        }}
        onReplaceSuccess={handleReplaceSuccess}
      />
    </div>
  );
};

export default TeamsTab;