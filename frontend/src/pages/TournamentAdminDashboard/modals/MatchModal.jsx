// frontend/src/pages/TournamentAdminDashboard/DashboardTabs/MatchModal.jsx
import { useState } from 'react';
import client from '../../../api/client';
import '../styles/MatchModal.css';

const MatchModal = ({ encounter, teams, onClose, onUpdate }) => {
  const [modalTab, setModalTab] = useState('result');
  const [manualScore, setManualScore] = useState({
    team1: encounter?.team1_score ?? '',
    team2: encounter?.team2_score ?? ''
  });
  const [logFile, setLogFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [replaceTeamId, setReplaceTeamId] = useState('');

  const teamName = (teamId) => {
    const team = teams.find(t => t.id === teamId);
    return team?.name || `Команда ${teamId}`;
  };

  const handleLogUpload = async () => {
    if (!logFile) return;
    setLoading(true);
    setUploadStatus('Загрузка...');

    const formData = new FormData();
    formData.append('file', logFile);
    formData.append('encounter_id', encounter.id);

    try {
      await client.post('/matches/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus('✅ Лог успешно обработан');
      setTimeout(() => {
        onClose();
        onUpdate();
      }, 1200);
    } catch (err) {
      setUploadStatus('❌ Ошибка загрузки лога');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSetResult = async () => {
    setLoading(true);
    try {
      await client.put(`/matches/admin/encounters/${encounter.id}/report-result`, {
        team1_score: parseInt(manualScore.team1) || 0,
        team2_score: parseInt(manualScore.team2) || 0,
      });
      onClose();
      onUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleForfeit = async (loserTeamId) => {
    if (!window.confirm('Вы уверены, что хотите поставить техническое поражение?')) return;
    
    setLoading(true);
    try {
      await client.put(`/matches/admin/encounters/${encounter.id}/forfeit/`, {
        loser_team_id: loserTeamId,
      });
      onClose();
      onUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReplaceTeam = async () => {
    if (!replaceTeamId) return;
    setLoading(true);
    try {
      const oldTeamId = encounter.team1_id === parseInt(replaceTeamId) 
        ? encounter.team2_id 
        : encounter.team1_id;

      await client.put(`/matches/admin/encounters/${encounter.id}/replace/`, {
        old_team_id: oldTeamId,
        new_team_id: parseInt(replaceTeamId),
      });
      onClose();
      onUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Удалить матч? Это может сломать сетку.')) return;
    setLoading(true);
    try {
      await client.delete(`/matches/admin/encounters/${encounter.id}/`);
      onClose();
      onUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!encounter) return null;

  const isCompleted = !!encounter.winner_team_id;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Управление матчем</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-tabs">
          <button className={`modal-tab ${modalTab === 'result' ? 'active' : ''}`} onClick={() => setModalTab('result')}>
            Результат
          </button>
          <button className={`modal-tab ${modalTab === 'settings' ? 'active' : ''}`} onClick={() => setModalTab('settings')}>
            Настройки
          </button>
        </div>

        <div className="modal-body">
          <div className="match-info">
            <strong>{encounter.stage}</strong> • Раунд {encounter.round_number}
          </div>

          {/* Команды */}
          <div className="match-teams">
            <div className={`team-side ${encounter.winner_team_id === encounter.team1_id ? 'winner' : ''}`}>
              <h4>{teamName(encounter.team1_id)}</h4>
            </div>
            <div className="vs-score">
              {encounter.team1_score ?? '?'} : {encounter.team2_score ?? '?'}
            </div>
            <div className={`team-side ${encounter.winner_team_id === encounter.team2_id ? 'winner' : ''}`}>
              <h4>{teamName(encounter.team2_id)}</h4>
            </div>
          </div>

          {modalTab === 'result' && !isCompleted && (
            <>
              <div className="modal-section">
                <h4>Загрузить лог матча</h4>
                <input type="file" accept=".txt,.csv" onChange={e => setLogFile(e.target.files[0])} />
                <button onClick={handleLogUpload} disabled={loading || !logFile} className="btn-primary">
                  Загрузить и обработать
                </button>
                {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
              </div>

              <div className="modal-section">
                <h4>Ввести результат вручную</h4>
                <div className="score-inputs">
                  <input
                    type="number"
                    value={manualScore.team1}
                    onChange={e => setManualScore(prev => ({...prev, team1: e.target.value}))}
                    placeholder="Счёт команды 1"
                  />
                  <input
                    type="number"
                    value={manualScore.team2}
                    onChange={e => setManualScore(prev => ({...prev, team2: e.target.value}))}
                    placeholder="Счёт команды 2"
                  />
                </div>
                <button onClick={handleSetResult} disabled={loading} className="btn-primary">
                  Сохранить результат
                </button>
              </div>

              <div className="modal-section danger">
                <h4>Техническое поражение</h4>
                <button onClick={() => handleForfeit(encounter.team1_id)} disabled={loading}>
                  Поражение {teamName(encounter.team1_id)}
                </button>
                <button onClick={() => handleForfeit(encounter.team2_id)} disabled={loading}>
                  Поражение {teamName(encounter.team2_id)}
                </button>
              </div>
            </>
          )}

          {modalTab === 'settings' && (
            <div className="modal-section">
              <h4>Замена команды</h4>
              <select value={replaceTeamId} onChange={e => setReplaceTeamId(e.target.value)}>
                <option value="">Выберите команду...</option>
                {teams.map(team => (
                  <option key={team.id} value={team.id}>{team.name}</option>
                ))}
              </select>
              <button onClick={handleReplaceTeam} disabled={loading || !replaceTeamId} className="btn-primary">
                Заменить команду
              </button>

              <div className="danger-zone">
                <h4>Удаление матча</h4>
                <button onClick={handleDelete} disabled={loading} className="btn-danger">
                  Удалить матч
                </button>
                <p className="warning-text">Это действие может нарушить структуру турнира.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MatchModal;