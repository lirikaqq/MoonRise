import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../../context/AuthContext';
import tournamentsApi from '../../../api/tournaments';
import { CheckCircle, XCircle, Crown, Plus } from 'lucide-react';
import AdminAddParticipantModal from '../modals/AdminAddParticipantModal';
import '../styles/ApplicationsTab.css';

const REJECT_TEMPLATES = [
  'Низкий рейтинг',
  'Не указан Discord',
  'Не прошёл Check-in',
  'Подозрение на буст/накрутку',
  'Нарушение правил регистрации',
  'Другая причина'
];

const parseApplicationData = (app) => {
  if (!app) return { discord: '—', battletag: '—', displayName: '—', primaryRole: '—', secondaryRole: '—', notes: '', isCaptain: false };

  const data = app.application_data || {};
  const username = (app.user_display_name || app.user_username || '').trim();

  const battletag = data.battletag_value || data.battletag || '—';
  // FIX: Prioritize discord_tag over username for Discord display
  const discord = data.discord_tag || username || '—';

  const primaryRole = data.primary_role || '—';
  const secondaryRole = data.secondary_role || '—';
  const notes = (data.bio || data.notes || '').trim();

  const isCaptain = app.is_captain === true || data.want_to_be_captain === 'Да';
  const displayName = battletag !== '—' ? battletag.split('#')[0] : discord;

  return { discord, battletag, displayName, primaryRole, secondaryRole, notes, isCaptain };
};

const ApplicationsTab = ({ tournamentId, onRefresh }) => {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('pending');

  const [rejectModal, setRejectModal] = useState({ isOpen: false, application: null, reason: '' });
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const loadApplications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await tournamentsApi.getApplications(
        tournamentId,
        statusFilter === 'all' ? null : statusFilter
      );
      setApplications(res.applications || []);
      setSelectedIds([]);
    } catch (err) {
      console.error('Ошибка загрузки заявок:', err);
    } finally {
      setLoading(false);
    }
  }, [tournamentId, statusFilter]);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  const filteredApplications = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return applications;
    return applications.filter(app => {
      const d = parseApplicationData(app);
      const text = `${d.displayName} ${d.discord} ${d.battletag} ${d.notes}`.toLowerCase();
      return text.includes(q);
    });
  }, [applications, searchQuery]);

  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleAddSuccess = () => {
    loadApplications();
    onRefresh?.();
  };

  const handleApprove = async (app) => {
    setActionLoading(app.user_id);
    try {
      await tournamentsApi.approveApplication(tournamentId, app.user_id);
      await loadApplications();
      onRefresh?.();
    } catch (err) {
      alert('Ошибка при одобрении');
    } finally {
      setActionLoading(null);
    }
  };

  const handleBulkApprove = async () => {
    if (!selectedIds.length || !window.confirm(`Одобрить ${selectedIds.length} заявок?`)) return;
    setActionLoading('bulk');
    try {
      await Promise.all(selectedIds.map(id => tournamentsApi.approveApplication(tournamentId, id)));
      alert('Выбранные заявки одобрены');
      setSelectedIds([]);
      await loadApplications();
      onRefresh?.();
    } catch (err) {
      alert('Ошибка при одобрении');
    } finally {
      setActionLoading(null);
    }
  };

  const handleBulkReject = async () => {
    if (!selectedIds.length) return;
    const reason = prompt('Укажите причину отклонения выбранных заявок:');
    if (reason === null) return;

    setActionLoading('bulk');
    try {
      await Promise.all(
        selectedIds.map(id => tournamentsApi.rejectApplication(tournamentId, id, reason || 'Отклонено администратором'))
      );
      alert('Выбранные заявки отклонены');
      setSelectedIds([]);
      await loadApplications();
      onRefresh?.();
    } catch (err) {
      alert('Ошибка при отклонении');
    } finally {
      setActionLoading(null);
    }
  };

  const handleApproveAll = async () => {
    if (!window.confirm('Одобрить ВСЕ заявки на рассмотрении?')) return;
    setActionLoading('all');
    try {
      await Promise.all(
        applications
          .filter(a => a.status === 'pending')
          .map(a => tournamentsApi.approveApplication(tournamentId, a.user_id))
      );
      alert('Все заявки одобрены');
      await loadApplications();
      onRefresh?.();
    } catch (err) {
      alert('Ошибка');
    } finally {
      setActionLoading(null);
    }
  };

  const copyToClipboard = (text) => {
    if (!text || text === '—') return;
    navigator.clipboard.writeText(text);
    alert(`Скопировано: ${text}`);
  };

  const openRejectModal = (app) => {
    setRejectModal({ isOpen: true, application: app, reason: '' });
  };

  const handleSingleReject = async () => {
    const { application, reason } = rejectModal;
    if (!reason) return alert('Укажите причину');

    setActionLoading(application.user_id);
    try {
      await tournamentsApi.rejectApplication(tournamentId, application.user_id, reason);
      setRejectModal({ isOpen: false, application: null, reason: '' });
      await loadApplications();
      onRefresh?.();
    } catch (err) {
      alert('Ошибка при отклонении');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <div className="admin-skeleton">Загрузка заявок...</div>;

  const pendingCount = applications.filter(a => a.status === 'pending').length;

  return (
    <div className="applications-tab">
      <div className="admin-toolbar">
        <input
          type="text"
          className="admin-search-input"
          placeholder="Поиск по нику, Discord или Battletag..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        <div className="admin-filters">
          {['pending', 'registered', 'rejected', 'all'].map(s => (
            <button
              key={s}
              className={`filter-btn ${statusFilter === s ? 'active' : ''}`}
              onClick={() => setStatusFilter(s)}
            >
              {s === 'pending' ? 'На рассмотрении' : s === 'registered' ? 'Одобрены' : s === 'rejected' ? 'Отклонены' : 'Все'}
            </button>
          ))}
        </div>

        <button 
          className="btn btn-primary admin-add-btn"
          onClick={() => setIsAddModalOpen(true)}
        >
          <Plus size={18} />
          Добавить участника
        </button>

        {selectedIds.length > 0 && (
          <div className="bulk-actions">
            <span>{selectedIds.length} выбрано</span>
            <button className="btn btn-approve" onClick={handleBulkApprove}>
              Принять выбранные
            </button>
            <button className="btn btn-reject" onClick={handleBulkReject}>
              Отклонить выбранные
            </button>
          </div>
        )}
      </div>

      <div className="applications-list">
        {filteredApplications.map(app => {
          const data = parseApplicationData(app);
          const isSelected = selectedIds.includes(app.user_id);
          const isPending = app.status === 'pending';

          return (
            <div key={app.user_id} className={`application-card ${isSelected ? 'selected' : ''}`}>
              <div className="card-checkbox">
                <input 
                  type="checkbox" 
                  checked={isSelected}
                  onChange={() => toggleSelect(app.user_id)}
                />
              </div>

              <div className="card-content">
                <div className="player-name">
                  {data.displayName}
                  {data.isCaptain && <Crown className="captain-icon" size={20} />}
                </div>

                <div className="player-tags">
                  <div className="tag discord" onClick={() => copyToClipboard(data.discord)}>
                    D: {data.discord}
                  </div>
                  <div className="tag battletag" onClick={() => copyToClipboard(data.battletag)}>
                    B: {data.battletag}
                  </div>
                </div>

                <div className="roles">
                  {data.primaryRole} / {data.secondaryRole}
                </div>

                {data.notes && <div className="notes">Заметки: {data.notes}</div>}
              </div>

              <div className="card-status">
                <span className={`status-badge ${app.status}`}>
                  {app.status === 'pending' && 'НА РАССМОТРЕНИИ'}
                  {app.status === 'registered' && 'ОДОБРЕНА'}
                  {app.status === 'rejected' && 'ОТКЛОНЕНА'}
                </span>
              </div>

              <div className="card-actions">
                {isPending && (
                  <>
                    <button 
                      className="btn btn-approve" 
                      onClick={() => handleApprove(app)}
                      disabled={actionLoading === app.user_id}
                    >
                      Принять
                    </button>
                    <button 
                      className="btn btn-reject" 
                      onClick={() => openRejectModal(app)}
                    >
                      Отклонить
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {statusFilter === 'pending' && pendingCount > 0 && (
        <div className="bulk-all">
          <button className="btn btn-approve" onClick={handleApproveAll}>
            Принять всех ({pendingCount})
          </button>
        </div>
      )}

      {/* Модалка добавления участника */}
      <AdminAddParticipantModal
        tournamentId={tournamentId}
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={handleAddSuccess}
      />

      {/* Модалка отклонения */}
      {rejectModal.isOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Отклонение заявки</h3>
            <p><strong>{rejectModal.application?.user_display_name || rejectModal.application?.user_username}</strong></p>

            <select 
              className="reject-select" 
              value={rejectModal.reason} 
              onChange={e => setRejectModal(p => ({...p, reason: e.target.value}))}
            >
              <option value="">Выберите шаблон...</option>
              {REJECT_TEMPLATES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>

            <textarea
              placeholder="Или напишите свою причину..."
              value={rejectModal.reason}
              onChange={e => setRejectModal(p => ({...p, reason: e.target.value}))}
            />

            <div className="modal-buttons">
              <button 
                className="btn btn-cancel" 
                onClick={() => setRejectModal({ isOpen: false, application: null, reason: '' })}
              >
                Отмена
              </button>
              <button className="btn btn-reject" onClick={handleSingleReject}>
                Отклонить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationsTab;