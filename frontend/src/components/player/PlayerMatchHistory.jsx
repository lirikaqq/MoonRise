// frontend/src/components/player/PlayerMatchHistory.jsx

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPlayerMatchHistory } from '../../api/matches';
import KillFeed from '../match/KillFeed';
import './PlayerMatchHistory.css';

export default function PlayerMatchHistory({ userId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMatchId, setSelectedMatchId] = useState(null);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    getPlayerMatchHistory(userId)
      .then(setHistory)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <div className="history-loading">Загрузка истории матчей...</div>;
  if (error) return <div className="history-error">Ошибка: {error}</div>;
  if (history.length === 0) return <div className="history-empty">История матчей пуста.</div>;

  return (
    <div className="history-container">
      <h2 className="history-title">История матчей</h2>
      <table className="history-table">
        <thead>
          <tr>
            <th>Турнир / Карта</th>
            <th>Счёт</th>
            <th>K / D</th>
            <th>Герои</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {history.map(item => (
            <tr key={item.match_id} className={selectedMatchId === item.match_id ? 'history-row--selected' : ''}>
              <td>
                <div className="tournament-name">
                  <Link to={`/tournaments/${item.tournament_id}`}>{item.tournament_name}</Link>
                </div>
                <div className="map-name">{item.stage} &middot; {item.map_name}</div>
              </td>
              <td className="score">
                {item.team1_score} : {item.team2_score}
              </td>
              <td className="kda">
                {item.eliminations} / {item.deaths}
              </td>
              <td>
                <div className="history-heroes">
                  {item.heroes.slice(0, 5).map(heroName => (
                    <div key={heroName} className="history-hero-icon" title={heroName}>
                      {heroName.substring(0, 3).toUpperCase()}
                    </div>
                  ))}
                </div>
              </td>
              <td>
                <button
                  className="history-show-kf"
                  onClick={() => setSelectedMatchId(selectedMatchId === item.match_id ? null : item.match_id)}
                >
                  {selectedMatchId === item.match_id ? 'Скрыть' : 'Kill Feed'}
                </button>
                <Link
                  to={`/matches/${item.match_id}`}
                  state={{ from: { url: window.location.pathname, label: 'PLAYER PROFILE' } }}
                  className="history-match-link"
                >
                  Детали →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Kill Feed для выбранного матча */}
      {selectedMatchId && (
        <div className="history-killfeed-wrap">
          <KillFeed matchId={selectedMatchId} />
        </div>
      )}
    </div>
  );
}