import { useState, useEffect, useCallback } from 'react';
import { Users, UserPlus, Shuffle, X } from 'lucide-react';
import tournamentsApi from '../../../api/tournaments';
import '../styles/ReplacePlayerModal.css';

export default function ReplacePlayerModal({
  tournamentId,
  playerToReplace,
  isOpen,
  onClose,
  onReplaceSuccess,
}) {
  const [option, setOption] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = useCallback(async (query) => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      let res;
      if (option === 'system') {
        res = await tournamentsApi.searchUsers(query);
        setResults(res.users || []);
      } else if (option === 'tournament') {
        res = await tournamentsApi.searchTournamentPlayers(tournamentId, query);
        setResults(res.participants || []);
      }
    } catch (err) {
      console.error('Search error:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [option, tournamentId]);

  useEffect(() => {
    if (searchQuery) handleSearch(searchQuery);
  }, [searchQuery, handleSearch]);

  const selectPlayer = async (player) => {
    if (!playerToReplace) return;

    const newUserId = player.user_id || player.id;
    if (!newUserId) return alert('Не удалось получить ID пользователя');

    try {
      await tournamentsApi.replacePlayer(
        tournamentId,
        playerToReplace.teamId, 
        playerToReplace.playerId,
        newUserId
      );
      onReplaceSuccess(player, option);
    } catch (err) {
      alert('Ошибка при замене игрока: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRandomReplace = async () => {
    if (!freePlayers || freePlayers.length === 0) {
      return alert('Нет свободных игроков');
    }
    const random = freePlayers[Math.floor(Math.random() * freePlayers.length)];
    const newUserId = random.user_id || random.id;
    if (!newUserId) return alert('Не удалось получить ID');

    try {
      await tournamentsApi.replacePlayer(
        tournamentId,
        playerToReplace.teamId,
        playerToReplace.playerId,
        newUserId
      );
      onReplaceSuccess(random, 'random');
    } catch (err) {
      alert('Ошибка при случайной замене');
    }
  };

  if (!isOpen || !playerToReplace) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content replace-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}><X size={26} /></button>

        <h2 className="modal-title">Замена игрока</h2>
        <p className="modal-subtitle">
          Заменяем: <strong>{playerToReplace.playerName}</strong>
        </p>

        {!option ? (
          <div className="replace-options">
            <div className="replace-option" onClick={() => setOption('system')}>
              <Users size={42} />
              <h3>Из системы</h3>
              <p>Поиск по всем пользователям</p>
            </div>

            <div className="replace-option" onClick={() => setOption('tournament')}>
              <Users size={42} />
              <h3>Из турнира</h3>
              <p>По Discord или BattleTag</p>
            </div>

            <div className="replace-option" onClick={handleRandomReplace}>
              <Shuffle size={42} />
              <h3>Случайная замена</h3>
              <p>Из свободных игроков</p>
            </div>
          </div>
        ) : (
          <div className="search-mode">
            <input
              type="text"
              placeholder="Поиск по никнейму, Discord или BattleTag..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              autoFocus
            />

            <div className="search-results">
              {loading ? (
                <div className="loading">Поиск...</div>
              ) : results.length === 0 ? (
                <div className="no-results">Ничего не найдено</div>
              ) : (
                results.map(player => (
                  <div 
                    key={player.user_id || player.id}
                    className="search-result-item"
                    onClick={() => selectPlayer(player)}
                  >
                    <strong>{player.user_display_name || player.display_name || player.username}</strong>
                    <span className="small">
                      {player.application_data?.battletag_value || player.battletag_value || ''}
                    </span>
                  </div>
                ))
              )}
            </div>

            <button className="btn-secondary" onClick={() => {
              setOption(null);
              setSearchQuery('');
              setResults([]);
            }}>
              Назад к выбору
            </button>
          </div>
        )}
      </div>
    </div>
  );
}