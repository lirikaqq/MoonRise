// frontend/src/pages/TournamentAdminDashboard/DashboardTabs/ManagementTab.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Play, RotateCcw, Trash2, Users } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import tournamentsApi from '../../../api/tournaments';
import { draftApi } from '../../../api/draft';
import { seedParticipants, resetDraft, deleteAllParticipants } from '../../../api/dev';
import client from '../../../api/client';
import '../styles/ManagementTab.css';

const ManagementTab = ({ tournamentId, tournament, onUpdate }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isDev = import.meta.env.DEV;

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState('info'); // 'success' | 'error'
  const [draftSession, setDraftSession] = useState(null);

  const showMessage = (text, type = 'info') => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => setMessage(null), 5000);
  };

  const changeStatus = async (newStatus) => {
    setLoading(true);
    try {
      await tournamentsApi.updateStatus(tournamentId, newStatus);
      showMessage(`Статус изменён на "${newStatus}"`, 'success');
      onUpdate();
    } catch (err) {
      showMessage('Ошибка при смене статуса', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadDraftSession = async () => {
    try {
      const data = await tournamentsApi.getById(tournamentId);
      setDraftSession(data.draft_session || null);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (tournament.format === 'draft') {
      loadDraftSession();
    }
  }, [tournament]);

  const handleStartDraft = async () => {
    setLoading(true);
    try {
      let sessionId = draftSession?.id;

      if (!sessionId) {
        const captainsRes = await client.get(`/tournaments/${tournamentId}/captains/`);
        const captains = captainsRes.data?.captains || [];

        if (captains.length < 2) {
          showMessage('Нужно минимум 2 капитана. Назначьте их во вкладке "ЗАЯВКИ"', 'error');
          setLoading(false);
          return;
        }

        const captainUserIds = captains.map(c => c.user_id);
        const teamNames = {};
        captains.forEach(c => {
          teamNames[c.user_id] = c.display_name || c.username;
        });

        const setupResult = await draftApi.setupDraft(tournamentId, {
          captain_user_ids: captainUserIds,
          team_names: teamNames,
          pick_time_seconds: 90,
          team_size: tournament.team_config?.team_size || 5,
          role_slots: tournament.team_config?.roles || { tank: 1, dps: 2, support: 2 },
        });

        sessionId = setupResult.draft_session_id;
      }

      await draftApi.startDraft(sessionId);
      showMessage('Драфт успешно запущен!', 'success');
      
      setTimeout(() => {
        navigate(`/draft/${tournamentId}`);
      }, 1500);
    } catch (err) {
      showMessage(err.response?.data?.detail || 'Не удалось запустить драфт', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSwissRound = async () => {
    setLoading(true);
    try {
      await client.post(`/matches/admin/tournaments/${tournamentId}/swiss-next-round/`, { avoid_repeat: true });
      showMessage('Следующий тур швейцарской системы создан', 'success');
      onUpdate();
    } catch (err) {
      showMessage('Ошибка генерации раунда', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDangerAction = async (action, confirmText, successText) => {
    if (!window.confirm(confirmText)) return;

    setLoading(true);
    try {
      let result;
      if (action === 'seed') result = await seedParticipants(tournamentId);
      else if (action === 'resetDraft') result = await resetDraft(tournamentId);
      else if (action === 'deleteParticipants') result = await deleteAllParticipants(tournamentId);
      else if (action === 'deleteTournament') {
        await tournamentsApi.delete(tournamentId);
        navigate('/admin/tournaments');
        return;
      }

      showMessage(successText || result?.message || 'Операция выполнена', 'success');
      onUpdate();
    } catch (err) {
      showMessage(err.response?.data?.detail || 'Ошибка выполнения', 'error');
    } finally {
      setLoading(false);
    }
  };

  const statusActions = {
    upcoming: { to: 'registration', label: 'Открыть регистрацию' },
    registration: { to: 'checkin', label: 'Открыть Check-in' },
    checkin: { to: 'ongoing', label: 'Начать турнир' },
    draft: { to: 'ongoing', label: 'Завершить драфт и начать турнир' },
    ongoing: { to: 'completed', label: 'Завершить турнир' },
  };

  const nextAction = statusActions[tournament.status];

  return (
    <div className="management-tab">
      {message && (
        <div className={`admin-message admin-message--${messageType}`}>
          {message}
        </div>
      )}

      {/* Статус турнира */}
      <div className="management-section">
        <h3>Статус турнира</h3>
        <p className="current-status">
          Текущий статус: <strong>{tournament.status}</strong>
        </p>
        
        {nextAction && (
          <button
            className="btn btn-primary btn-large"
            onClick={() => changeStatus(nextAction.to)}
            disabled={loading}
          >
            {nextAction.label}
          </button>
        )}
      </div>

      {/* Драфт */}
      {tournament.format === 'draft' && (
        <div className="management-section">
          <h3>🎤 Управление драфтом</h3>
          {draftSession ? (
            <div className="draft-info">
              <p>Сессия драфта: <strong>{draftSession.status}</strong></p>
              {draftSession.status === 'pending' && (
                <button
                  className="btn btn-primary"
                  onClick={handleStartDraft}
                  disabled={loading}
                >
                  <Play size={18} /> Запустить драфт
                </button>
              )}
              {(draftSession.status === 'in_progress' || draftSession.status === 'completed') && (
                <button
                  className="btn btn-primary"
                  onClick={() => navigate(`/draft/${tournamentId}`)}
                >
                  Перейти к драфту
                </button>
              )}
            </div>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleStartDraft}
              disabled={loading}
            >
              Настроить и запустить драфт
            </button>
          )}
        </div>
      )}

      {/* Swiss System */}
      {tournament.structure_type?.includes('SWISS') && (
        <div className="management-section">
          <h3>Швейцарская система</h3>
          <button
            className="btn btn-primary"
            onClick={handleGenerateSwissRound}
            disabled={loading}
          >
            🔄 Сгенерировать следующий тур
          </button>
        </div>
      )}

      {/* Dev Tools */}
      {isDev && user?.role === 'admin' && (
        <div className="management-section dev-section">
          <h3>🛠 Dev Tools</h3>
          <div className="dev-buttons">
            <button
              className="btn btn-outline"
              onClick={() => handleDangerAction('seed', 'Создать 10 тестовых участников?', 'Участники добавлены')}
            >
              <Users size={18} /> Seed Participants
            </button>
            <button
              className="btn btn-danger-outline"
              onClick={() => handleDangerAction('resetDraft', 'Сбросить драфт?', 'Драфт сброшен')}
            >
              <RotateCcw size={18} /> Reset Draft
            </button>
            <button
              className="btn btn-danger-outline"
              onClick={() => handleDangerAction('deleteParticipants', 'Удалить ВСЕХ участников?', 'Все участники удалены')}
            >
              <Trash2 size={18} /> Delete All Participants
            </button>
          </div>
        </div>
      )}

      {/* Danger Zone */}
      <div className="management-section danger-zone">
        <h3>
          <AlertTriangle size={20} /> Опасная зона
        </h3>
        <button
          className="btn btn-danger btn-large"
          onClick={() => handleDangerAction('deleteTournament', 'Вы уверены, что хотите УДАЛИТЬ турнир полностью? Это действие необратимо!', null)}
        >
          <Trash2 size={20} /> Удалить турнир
        </button>
      </div>
    </div>
  );
};

export default ManagementTab;