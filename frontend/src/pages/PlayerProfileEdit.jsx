import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { playersApi } from '../api/players';
import { useAuth } from '../context/AuthContext';
import './PlayerProfileEdit.css';

export default function PlayerProfileEdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  
  const [battletag, setBattletag] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Защита: только владелец может редактировать
  useEffect(() => {
    if (loading || !currentUser) return;
    if (currentUser.id !== parseInt(id)) {
      navigate(`/players/${id}`); // Редирект, если не владелец
    }
  }, [currentUser, id, loading, navigate]);
  
  // Загрузка текущих данных
  useEffect(() => {
    playersApi.getById(id)
      .then(playerData => {
        const primaryTag = playerData.battletags?.find(t => t.is_primary) || playerData.battletags?.[0];
        if (primaryTag) {
          setBattletag(primaryTag.tag);
        }
        setLoading(false);
      })
      .catch(() => {
        setError('Не удалось загрузить профиль');
        setLoading(false);
      });
  }, [id]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await playersApi.update(id, { primary_battletag: battletag });
      navigate(`/players/${id}`); // Возвращаемся в профиль после сохранения
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Загрузка...</div>;

  return (
    <div className="edit-profile-page">
      <div className="edit-profile-container">
        <h1>Редактировать профиль</h1>
        
        {error && <div style={{color: 'red', marginBottom: '1rem'}}>{error}</div>}

        <form onSubmit={handleSave}>
          <div className="form-group">
            <label htmlFor="battletag" className="form-label">
              Основной BattleTag
            </label>
            <input
              id="battletag"
              type="text"
              className="form-input"
              value={battletag}
              onChange={(e) => setBattletag(e.target.value)}
              placeholder="Player#12345"
            />
            <p style={{fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem'}}>
              Этот тег будет использоваться для автоматического сбора статистики из логов.
            </p>
          </div>

          <div className="form-actions">
            <button type="submit" className="button primary" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="button secondary" onClick={() => navigate(`/players/${id}`)}>
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}