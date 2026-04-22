// frontend/src/components/draft/DraftTeamsPanel.jsx
import React, { useMemo } from 'react';

export default function DraftTeamsPanel({ captains, picks }) {
  // useMemo, чтобы не пересчитывать на каждый рендер
  const teamsData = useMemo(() => {
    // Создаем карту пиков по ID капитана для быстрого доступа
    const picksByCaptain = picks.reduce((acc, pick) => {
      if (!acc[pick.captain_id]) {
        acc[pick.captain_id] = [];
      }
      acc[pick.captain_id].push(pick);
      return acc;
    }, {});

    // Для каждого капитана добавляем его пики
    return captains.map(captain => ({
      ...captain,
      players: picksByCaptain[captain.id] || []
    }));
  }, [captains, picks]);

  return (
    <>
      <h2>КОМАНДЫ</h2>

      <div>
        {teamsData.map((team) => (
          <div key={team.id} className="team-card">
            <div className="team-header">
              <div className="team-header-info">
                  <div className="team-name" title={team.team_name}>{team.team_name}</div>
                  <div className="captain-name">Captain: {team.username}</div>
              </div>
            </div>

            <ul className="player-list">
              {/* Рендерим игроков, которых выбрала эта команда */}
              {team.players.map(player => (
                <li key={player.pick_number} className="player-row">
                  <span className="player-role-badge">{player.assigned_role}</span>
                  <span className="player-name" title={player.picked_user_name}>{player.picked_user_name}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}