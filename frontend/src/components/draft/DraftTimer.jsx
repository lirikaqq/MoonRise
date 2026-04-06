// frontend/src/components/draft/DraftTimer.jsx
import React, { useState, useEffect, useMemo } from 'react';

export default function DraftTimer({ draftState, currentUser, isConnected }) {
  const [timeLeft, setTimeLeft] = useState(null);

  // Определяем, чей сейчас ход
  const currentPickData = useMemo(() => {
    if (!draftState || draftState.status !== 'in_progress') return null;
    
    // Если драфт закончился
    if (draftState.current_pick_index >= draftState.pick_order.length) return null;

    const captainUserId = draftState.pick_order[draftState.current_pick_index];
    const team = draftState.captains.find(c => c.user_id === captainUserId);
    const isMyTurn = currentUser?.id === captainUserId;

    return { team, isMyTurn };
  }, [draftState, currentUser]);

  // Логика обратного отсчета
  useEffect(() => {
    // Если драфт не идет или нет дедлайна - сбрасываем таймер
    if (!draftState?.current_pick_deadline || draftState.status !== 'in_progress') {
      setTimeLeft(null);
      return;
    }

    const calculateTimeLeft = () => {
      // Преобразуем строку ISO из базы в timestamp
      const deadline = new Date(draftState.current_pick_deadline).getTime();
      const now = Date.now();
      const diffSeconds = Math.floor((deadline - now) / 1000);
      
      return diffSeconds > 0 ? diffSeconds : 0;
    };

    // Устанавливаем сразу, чтобы не ждать 1 секунду
    setTimeLeft(calculateTimeLeft());

    const intervalId = setInterval(() => {
      const newTimeLeft = calculateTimeLeft();
      setTimeLeft(newTimeLeft);
      
      // Если время вышло, можно остановить интервал (бэкенд сам сделает авто-пик)
      if (newTimeLeft <= 0) {
        clearInterval(intervalId);
      }
    }, 1000);

    return () => clearInterval(intervalId);
  }, [draftState?.current_pick_deadline, draftState?.status]);


  // --- Рендеринг для разных статусов ---

  if (!draftState) return null;

  if (draftState.status === 'pending') {
    return (
      <div className="draft-top-bar" style={{ justifyContent: 'center' }}>
        <h2 className="text-2xl font-bold text-gray-400">WAITING FOR DRAFT TO START...</h2>
      </div>
    );
  }

  if (draftState.status === 'completed') {
    return (
      <div className="draft-top-bar" style={{ justifyContent: 'center', backgroundColor: 'rgba(19, 200, 176, 0.1)' }}>
        <h2 className="text-3xl font-bold text-[var(--accent)]">DRAFT COMPLETED</h2>
      </div>
    );
  }

  // Рендеринг для in_progress
  if (currentPickData && currentPickData.team) {
    const isWarning = timeLeft !== null && timeLeft <= 15; // Красный таймер, если < 15 сек

    return (
      <div className="draft-top-bar">
        
        {/* Инфо о текущей команде */}
        <div className="draft-status-info">
          <div className="draft-turn-label">
            Current Pick (Round {Math.floor(draftState.current_pick_index / draftState.captains.length) + 1})
          </div>
          <div className="draft-current-team">{currentPickData.team.team_name}</div>
          <div className="draft-current-captain">Picking: {currentPickData.team.username}</div>
        </div>

        {/* Таймер */}
        <div className="draft-timer-container">
          <div className={`draft-timer-value ${isWarning ? 'draft-timer-warning' : ''}`}>
            {timeLeft !== null ? `0:${timeLeft.toString().padStart(2, '0')}` : '--:--'}
          </div>
          
          {/* Плашка "Твой ход" */}
          {currentPickData.isMyTurn && (
            <div className="draft-my-turn-badge">
              YOUR TURN TO PICK!
            </div>
          )}
        </div>

      </div>
    );
  }

  return null;
}