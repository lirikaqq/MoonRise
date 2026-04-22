import { useState, useEffect, useRef } from 'react';
import { Users, UserPlus, X } from 'lucide-react';
import tournamentsApi from '../../../api/tournaments';
import RoleSelector from '../../../components/RoleSelector/RoleSelector';
import BattleTagSelector from '../../../components/BattleTagSelector/BattleTagSelector';
import '../styles/AdminAddParticipantModal.css';

export default function AdminAddParticipantModal({
  tournamentId,
  isOpen,
  onClose,
  onSuccess,
}) {
  const [step, setStep] = useState('choose'); // 'choose', 'existing', 'new'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const timeoutRef = useRef(null);

  const [formData, setFormData] = useState({
    username: '',
    discord_tag: '',
    battletag_value: '',
    primary_role: '',
    secondary_role: '',
    division: '',
    bio: '',
    is_captain: false,
  });

  const resetModal = () => {
    setStep('choose');
    setSuggestions([]);
    setShowSuggestions(false);
    setFormData({
      username: '', discord_tag: '', battletag_value: '', primary_role: '',
      secondary_role: '', division: '', bio: '', is_captain: false
    });
    setError('');
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  // Поиск пользователей с debounce
  const searchUsers = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const res = await tournamentsApi.searchUsers(query);
      setSuggestions(res.users || []);
      setShowSuggestions(true);
    } catch (err) {
      console.error('Search error:', err);
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleUsernameChange = (e) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, username: value }));

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => searchUsers(value), 350);
  };

  const selectSuggestion = (user) => {
    setFormData(prev => ({
      ...prev,
      username: user.username,
      discord_tag: user.discord_tag || prev.discord_tag,
    }));
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.username || !formData.primary_role || !formData.battletag_value) {
      setError('Username, роль и BattleTag обязательны');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await tournamentsApi.addParticipant(tournamentId, {
        username: formData.username.trim(),
        discord_tag: formData.discord_tag.trim() || null,
        battletag_value: formData.battletag_value.trim(),
        primary_role: formData.primary_role,
        secondary_role: formData.secondary_role || null,
        division: formData.division ? parseInt(formData.division) : null,
        bio: formData.bio.trim() || null,
        is_captain: formData.is_captain,
      });

      onSuccess?.();
      handleClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Не удалось добавить участника');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content admin-add-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={handleClose}><X size={26} /></button>

        <h2 className="modal-title">ДОБАВИТЬ УЧАСТНИКА</h2>
        <p className="modal-subtitle">Турнир #{tournamentId}</p>

        {step === 'choose' && (
          <div className="choice-container">
            <div className="choice-card" onClick={() => setStep('existing')}>
              <Users size={48} />
              <h3>Существующий пользователь</h3>
              <p>Уже есть в системе</p>
            </div>
            <div className="choice-card" onClick={() => setStep('new')}>
              <UserPlus size={48} />
              <h3>Новый пользователь</h3>
              <p>Создать ghost-аккаунт</p>
            </div>
          </div>
        )}

        {(step === 'existing' || step === 'new') && (
          <form onSubmit={handleSubmit} className="admin-add-form">
            <div className="form-group" style={{ position: 'relative' }}>
              <label>Username / Никнейм *</label>
              <input
                type="text"
                value={formData.username}
                onChange={handleUsernameChange}
                placeholder="Начните вводить никнейм..."
                className="form-input"
                autoComplete="off"
                required
              />

              {showSuggestions && suggestions.length > 0 && (
                <div className="suggestions-list">
                  {suggestions.map(user => (
                    <div
                      key={user.id}
                      className="suggestion-item"
                      onClick={() => selectSuggestion(user)}
                    >
                      <strong>{user.display_name}</strong>
                      <span className="username"> (@{user.username})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {step === 'new' && (
              <div className="form-group">
                <label>Discord тег</label>
                <input
                  type="text"
                  value={formData.discord_tag}
                  onChange={(e) => setFormData(prev => ({ ...prev, discord_tag: e.target.value }))}
                  placeholder="username#1234"
                  className="form-input"
                />
              </div>
            )}

            <div className="form-group">
              <label>BattleTag *</label>
              <input
                type="text"
                value={formData.battletag_value}
                onChange={(e) => setFormData(prev => ({ ...prev, battletag_value: e.target.value }))}
                placeholder="Name#12345"
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label>Division (примерный)</label>
              <input
                type="number"
                value={formData.division}
                onChange={(e) => setFormData(prev => ({ ...prev, division: e.target.value }))}
                placeholder="1–20"
                min="1"
                max="20"
                className="form-input"
              />
            </div>

            <RoleSelector
              primaryRole={formData.primary_role}
              secondaryRole={formData.secondary_role}
              onPrimaryChange={(val) => setFormData(prev => ({ ...prev, primary_role: val }))}
              onSecondaryChange={(val) => setFormData(prev => ({ ...prev, secondary_role: val }))}
              disabled={loading}
            />

            <div className="form-group">
              <label>О себе (необязательно)</label>
              <textarea
                value={formData.bio}
                onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                placeholder="Дополнительная информация..."
                className="form-textarea"
                rows={3}
              />
            </div>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.is_captain}
                onChange={(e) => setFormData(prev => ({ ...prev, is_captain: e.target.checked }))}
              />
              Назначить капитаном
            </label>

            {error && <div className="form-error">{error}</div>}

            <div className="form-actions">
              <button type="button" className="btn-secondary" onClick={() => setStep('choose')}>
                Назад к выбору
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Добавление...' : 'Добавить участника'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}