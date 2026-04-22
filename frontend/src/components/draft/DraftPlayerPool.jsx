// frontend/src/components/draft/DraftPlayerPool.jsx
import React, { useState, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';

// Компонент одной карточки игрока
const PlayerCard = ({ player, onPick, canPick }) => {
  return (
    <div className="player-card">
      <div className="player-card-header">
        <div className="player-card-name" title={player.username}>{player.username}</div>
        <div className="player-card-rating">{player.rating_approved}</div>
      </div>
      <div className="player-card-roles">
        <span>{player.primary_role}</span> / <span>{player.secondary_role}</span>
      </div>
      <button
        className="player-card-button"
        onClick={() => onPick(player)}
        disabled={!canPick}
      >
        {canPick ? 'ВЗЯТЬ' : '—'}
      </button>
    </div>
  );
};

export default function DraftPlayerPool({ players, currentUser, draftState, makePick }) {
  const [activeRoleFilter, setActiveRoleFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Определяем, может ли текущий пользователь делать пик
  const isMyTurn = useMemo(() => {
    if (!draftState || !currentUser || draftState.status !== 'in_progress') return false;
    const currentPickerId = draftState.pick_order[draftState.current_pick_index];
    // Админ может кликать в любой ход, обычные капитаны — только в свой
    if (currentUser.role === 'admin') return true;
    return currentUser.id === currentPickerId;
  }, [draftState, currentUser]);

  // Проверка: драфт запущен?
  const isDraftInProgress = draftState?.status === 'in_progress';

  // Фильтруем и ищем игроков
  const filteredPlayers = useMemo(() => {
    return players.filter(player => {
      // Фильтр по роли
      const roleMatch = activeRoleFilter === 'all' ||
                        player.primary_role === activeRoleFilter ||
                        player.secondary_role === activeRoleFilter;
      // Фильтр по поиску
      const searchMatch = player.username.toLowerCase().includes(searchQuery.toLowerCase());

      return roleMatch && searchMatch;
    });
  }, [players, activeRoleFilter, searchQuery]);

  const handlePick = async (player) => {
    // Определяем роль: primary или fallback на dps
    const assignedRole = player.primary_role !== 'flex' ? player.primary_role : 'dps';

    makePick({
        picked_user_id: player.user_id,
        assigned_role: assignedRole,
    });
  };

  const ROLES = ['all', 'tank', 'dps', 'support', 'flex'];

  return (
    <>
      <header className="player-pool-header">
        {/* Фильтры по ролям */}
        <div className="player-pool-filters">
          {ROLES.map(role => (
            <button
              key={role}
              className={activeRoleFilter === role ? 'active' : ''}
              onClick={() => setActiveRoleFilter(role)}
            >
              {role === 'all' ? 'Все' : role}
            </button>
          ))}
        </div>
        {/* Поиск */}
        <div className="player-pool-search">
          <input
            type="text"
            placeholder="Поиск игрока..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </header>

      <div className="player-pool-grid">
        {/* Показываем сообщение если драфт не запущен */}
        {!isDraftInProgress && (
          <div style={{
            textAlign: 'center',
            color: '#A7F2A2',
            gridColumn: '1 / -1',
            padding: '2rem 0',
            fontSize: '1.1rem',
          }}>
            ⏳ Драфт ещё не запущен. Ожидание...
          </div>
        )}

        {filteredPlayers.map(player => (
          <PlayerCard
            key={player.user_id}
            player={player}
            onPick={handlePick}
            canPick={isMyTurn && isDraftInProgress}
          />
        ))}
        {filteredPlayers.length === 0 && isDraftInProgress && (
            <p style={{ textAlign: 'center', color: '#6b7280', gridColumn: '1 / -1', padding: '2rem 0' }}>
              Нет игроков по текущим фильтрам
            </p>
        )}
      </div>
    </>
  );
}