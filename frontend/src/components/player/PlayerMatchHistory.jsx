// frontend/src/components/player/PlayerMatchHistory.jsx

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPlayerMatchHistory } from '../../api/matches';
import './PlayerMatchHistory.css';

export default function PlayerMatchHistory({ userId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    getPlayerMatchHistory(userId)
      .then(setHistory)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <div>Загрузка истории матчей...</div>;
  if (error) return <div style={{ color: 'red' }}>Ошибка: {error}</div>;
  if (history.length === 0) return <div>История матчей пуста.</div>;

  return (
    <div className="history-container">
      <h2>История матчей</h2>
      <table className="history-table">
        <thead>
          <tr>
            <th>Турнир / Карта</th>
            <th>Счёт</th>
            <th>K / D / A</th>
            <th>Герои</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {history.map(item => {
            const isWinner = (item.team1_score > item.team2_score && item.team1_name.includes(/*Имя команды игрока*/)) ||
                             (item.team2_score > item.team1_score && item.team2_name.includes(/*Имя команды игрока*/));
            // TODO: Определить результат (победа/поражение) на бэкенде
            
            return (
              <tr key={item.match_id}>
                <td>
                  <div className="tournament-name">
                    <Link to={`/tournaments/${item.tournament_id}`}>{item.tournament_name}</Link>
                  </div>
                  <div className="map-name">{item.stage} &middot; {item.map_name}</div>
                </td>
                <td className="score">
                  {item.team1_name} {item.team1_score} : {item.team2_score} {item.team2_name}
                </td>
                <td className="kda">
                  {item.kills} / {item.deaths} / {item.assists}
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
                  <Link to={`/matches/${item.match_id}`} className="match-link">
                    Детали →
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}