// frontend/src/pages/TournamentAdminDashboard/DashboardTabs/DevToolsTab.jsx
import { useState } from 'react';
import { Wrench, Users, RotateCcw, Trash2, CheckCircle } from 'lucide-react';
import { seedParticipants, resetDraft, deleteAllParticipants } from '../../../api/dev';
import client from '../../../api/client';
import "../styles/DevToolsTab.css";

const DevToolsTab = ({ tournamentId, onRefresh }) => {
  const [actions, setActions] = useState({});

  const runAction = async (actionKey, config) => {
    if (config.confirm && !window.confirm(config.confirm)) return;

    setActions(prev => ({
      ...prev,
      [actionKey]: { loading: true, status: 'loading', message: null }
    }));

    try {
      let result;

      switch (actionKey) {
        case 'seedPending':
          // Используем правильный путь из dev.js
          result = await client.post(`/dev/tournaments/${tournamentId}/seed-participants`);
          result = result.data;
          break;

        case 'seed':
          result = await seedParticipants(tournamentId);
          break;

        case 'resetDraft':
          result = await resetDraft(tournamentId);
          break;

        case 'deleteParticipants':
          result = await deleteAllParticipants(tournamentId);
          break;

        default:
          throw new Error('Неизвестное действие');
      }

      setActions(prev => ({
        ...prev,
        [actionKey]: { 
          loading: false, 
          status: 'success', 
          message: result?.message || result?.detail || 'Выполнено успешно!' 
        }
      }));

      onRefresh?.();
    } catch (err) {
      console.error(err);
      setActions(prev => ({
        ...prev,
        [actionKey]: {
          loading: false,
          status: 'error',
          message: err.response?.data?.detail || err.message || 'Ошибка (404 или сервер не ответил)'
        }
      }));
    }
  };

  const ActionButton = ({ actionKey, label, icon: Icon, color = 'primary', confirm }) => {
    const state = actions[actionKey] || {};
    const isLoading = state.loading;

    return (
      <div className="dev-action">
        <button
          className={`dev-btn dev-btn--${color}`}
          onClick={() => runAction(actionKey, { confirm })}
          disabled={isLoading}
        >
          {isLoading ? '⏳ Выполняется...' : (
            <>
              {Icon && <Icon size={18} />}
              {label}
            </>
          )}
        </button>

        {state.message && (
          <div className={`dev-result ${state.status}`}>
            {state.status === 'success' && <CheckCircle size={16} />}
            {state.message}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="devtools-tab">
      <div className="devtools-header">
        <Wrench size={28} />
        <h2>Dev Tools — E2E Testing</h2>
      </div>
      <p className="devtools-description">
        Нажми кнопку ниже, чтобы создать тестовых участников.<br />
        <strong>Пока все создаются в статусе "registered"</strong>. Позже добавим создание в "pending".
      </p>

      <div className="devtools-grid">
        <div className="devtools-section">
          <h3>Создание участников</h3>
          <ActionButton
            actionKey="seedPending"
            label="Создать 10 тестовых участников"
            icon={Users}
            color="primary"
            confirm="Создать 10 тестовых участников для турнира?"
          />
        </div>

        <div className="devtools-section">
          <h3>Опасные действия</h3>
          <ActionButton
            actionKey="resetDraft"
            label="Сбросить драфт"
            icon={RotateCcw}
            color="danger"
            confirm="Сбросить драфт?"
          />
          <ActionButton
            actionKey="deleteParticipants"
            label="Удалить всех участников"
            icon={Trash2}
            color="danger"
            confirm="Удалить ВСЕХ участников турнира?"
          />
        </div>
      </div>
    </div>
  );
};

export default DevToolsTab;