// frontend/src/pages/DraftPage.jsx

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDraft } from '../hooks/useDraft';
import { useAuth } from '../context/AuthContext';
import tournamentsApi from '../api/tournaments';

// Импортируем CSS
import './DraftPage.css';

// Импортируем наши компоненты-заглушки
import DraftPlayerPool from '../components/draft/DraftPlayerPool';
import DraftTeamsPanel from '../components/draft/DraftTeamsPanel';
import DraftTimer from '../components/draft/DraftTimer';


export default function DraftPage() {
  const { tournamentId } = useParams();
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState(null);
  const [loadingSession, setLoadingSession] = useState(true);
  const [completing, setCompleting] = useState(false);

  // Находим сессию драфта по ID турнира
  useEffect(() => {
    const findDraftSession = async () => {
      try {
        const tournament = await tournamentsApi.getById(tournamentId);
        console.debug('[DraftPage] Tournament loaded:', {
          tournamentId: tournament.id,
          draft_session_id: tournament.draft_session?.id,
          draft_session_status: tournament.draft_session?.status,
        });
        if (tournament?.draft_session?.id) {
          setSessionId(tournament.draft_session.id);
        } else {
          console.error('No draft session found for tournament', tournamentId);
        }
      } catch (e) {
        console.error('Failed to load tournament:', e);
      } finally {
        setLoadingSession(false);
      }
    };
    findDraftSession();
  }, [tournamentId]);

  const { draftState, loading, error, isConnected, makePick, completeDraft, completedTeams } = useDraft(sessionId);

  const handleCompleteDraft = async () => {
    if (!window.confirm('Завершить драфт и создать команды? Это действие необратимо.')) {
      return;
    }
    setCompleting(true);
    try {
      await completeDraft();
    } finally {
      setCompleting(false);
    }
  };

  if (loadingSession) return <div style={{ textAlign: 'center', color: 'white', marginTop: '5rem' }}>Загрузка драфта...</div>;
  if (!loadingSession && !sessionId) {
    return (
      <div style={{ textAlign: 'center', color: '#A7F2A2', marginTop: '5rem', maxWidth: '600px', margin: '5rem auto 0', padding: '2rem' }}>
        <h2 style={{ color: '#13AD91', marginBottom: '1rem' }}>⏳ Драфт не запущен</h2>
        <p>Для данного турнира ещё не создана сессия драфта.</p>
        <p style={{ fontSize: '0.9rem', color: '#6b7280', marginTop: '1rem' }}>
          Администратор должен настроить и запустить драфт на странице турнира.
        </p>
      </div>
    );
  }
  if (error) return <div style={{ textAlign: 'center', color: 'red', marginTop: '5rem' }}>{error}</div>;
  if (!draftState) return <div style={{ textAlign: 'center', color: 'gray', marginTop: '5rem' }}>Нет данных драфта.</div>;

  // Проверяем что пользователь — админ
  const isAdmin = user?.role === 'admin';

  return (
    <div className="draft-page">
      <div className="draft-component-placeholder" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <DraftTimer
            draftState={draftState}
            currentUser={user}
            isConnected={isConnected}
          />
          {/* Кнопка "Завершить драфт" — только для админа и когда драфт в процессе */}
          {isAdmin && draftState.status === 'in_progress' && (
            <button
              onClick={handleCompleteDraft}
              disabled={completing}
              style={{
                padding: '10px 24px',
                background: completing ? '#555' : '#13AD91',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: completing ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                fontFamily: 'ST-SimpleSquare, sans-serif',
              }}
            >
              {completing ? 'Завершение...' : 'Завершить драфт'}
            </button>
          )}
        </div>
      </div>

      {/* Сообщение о завершении драфта */}
      {completedTeams && (
        <div style={{
          textAlign: 'center',
          padding: '16px',
          background: 'rgba(19, 173, 145, 0.1)',
          border: '1px solid #13AD91',
          borderRadius: '8px',
          marginBottom: '1rem',
          color: '#A7F2A2',
          fontFamily: 'ST-SimpleSquare, sans-serif',
        }}>
          🎉 Драфт завершён! Создано команд: {completedTeams.length}
        </div>
      )}

      <main className="draft-main-area">
        <div className="draft-pool-container draft-component-placeholder">
          <DraftPlayerPool
            players={draftState.player_pool}
            currentUser={user}
            draftState={draftState}
            makePick={makePick}
          />
        </div>

        <aside className="draft-teams-container draft-component-placeholder">
          <DraftTeamsPanel
            captains={draftState.captains}
            picks={draftState.picks}
          />
        </aside>
      </main>
    </div>
  );
}
