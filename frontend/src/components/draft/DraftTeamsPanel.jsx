// frontend/src/components/draft/DraftTeamsPanel.jsx
import React, { useMemo } from 'react';

// Стили можно вынести в CSS
const styles = {
  teamCard: {
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '1rem',
    fontFamily: 'Montserrat, sans-serif', // <-- Основной шрифт для карточки
  },
  teamHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem', // Отступ между аватаркой (когда добавим) и текстом
    marginBottom: '0.75rem',
    paddingBottom: '0.75rem',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  teamName: {
    fontFamily: 'Palui, sans-serif', // <-- Оставляем кастомный шрифт для заголовка
    fontSize: '1.5rem', // Чуть больше
    color: 'var(--accent-light)',
    lineHeight: '1.2', // Управляем высотой строки
  },
  captainName: {
    fontSize: '0.8rem',
    color: 'rgba(255, 255, 255, 0.6)',
    textTransform: 'uppercase', // CAPTAIN: YEBVAIOTSUDA
    letterSpacing: '0.5px',
  },
  playerList: {
    listStyle: 'none',
    padding: 0,
    margin: '0.5rem 0 0 0', // Добавим отступ сверху
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  playerRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    padding: '0.5rem 0.75rem',
    borderRadius: '4px',
  },
  playerRole: {
    fontFamily: 'Montserrat, sans-serif',
    fontWeight: '700', // Жирный
    fontSize: '0.7rem',
    textTransform: 'uppercase',
    color: 'var(--accent)',
    border: '1px solid var(--accent)',
    borderRadius: '3px',
    padding: '2px 6px',
    minWidth: '40px',
    textAlign: 'center',
  },
  playerName: {
    fontFamily: 'Montserrat, sans-serif',
    fontWeight: '500', // Средний
    fontSize: '0.9rem',
  },
};

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
      <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--accent)', marginBottom: '1rem' }}>
        TEAMS
      </h2>

      <div>
        {teamsData.map((team) => (
          <div key={team.id} style={styles.teamCard}>
            <div style={styles.teamHeader}>
              {/* TODO: Добавить аватарку капитана */}
              <div>
                  <div style={styles.teamName}>{team.team_name}</div>
                  <div style={styles.captainName}>Captain: {team.username}</div>
              </div>
            </div>

            <ul style={styles.playerList}>
              {/* Рендерим игроков, которых выбрала эта команда */}
              {team.players.map(player => (
                <li key={player.pick_number} style={styles.playerRow}>
                  <span style={styles.playerRole}>{player.assigned_role}</span>
                  <span style={styles.playerName}>{player.picked_user_name}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}