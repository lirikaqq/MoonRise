// frontend/src/components/draft/DraftPlayerPool.jsx
import React, { useState, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext'; // Импортируем useAuth

// Компонент одной карточки игрока
const PlayerCard = ({ player, onPick, canPick }) => (
  <div className="player-card">
    <div className="player-card-header">
      <div className="player-card-name">{player.username}</div>
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
      {canPick ? 'PICK' : '—'}
    </button>
  </div>
);

export default function DraftPlayerPool({ players, currentUser, draftState, makePick }) {
  const [activeRoleFilter, setActiveRoleFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Определяем, может ли текущий пользователь делать пик
  const isMyTurn = useMemo(() => {
    if (!draftState || !currentUser || draftState.status !== 'in_progress') return false;
    const currentPickerId = draftState.pick_order[draftState.current_pick_index];
    return currentUser.id === currentPickerId;
  }, [draftState, currentUser]);

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

  const handlePick = (player) => {
    // TODO: Открыть модалку для выбора, на какую роль взять игрока (tank, dps, support)
    // А пока для теста просто пикаем на первую доступную роль
    alert(`Picking ${player.username}. In a real app, a role selection modal would appear here.`);
    
    // Временно захардкодим роль для теста
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
              {role}
            </button>
          ))}
        </div>
        {/* Поиск */}
        <div className="player-pool-search">
          <input
            type="text"
            placeholder="Search player..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input" // Используем стиль из DraftPage.css
          />
        </div>
      </header>

      <div className="player-pool-grid">
        {filteredPlayers.map(player => (
          <PlayerCard 
            key={player.user_id} 
            player={player}
            onPick={handlePick}
            canPick={isMyTurn}
          />
        ))}
        {filteredPlayers.length === 0 && (
            <p>No players match the current filters.</p>
        )}
      </div>
    </>
  );
}