import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import './AdminHomepageSettings.css';

export default function AdminHomepageSettings() {
  const navigate = useNavigate();
  const [tournaments, setTournaments] = useState([]);
  const [settings, setSettings] = useState({
    tournament_id: '',
    title: '',
    date_text: '',
    description: '',
    logo_url: '',
    hero_image_url: '',
    registration_text: '',
    registration_url: '',
    info_text: '',
    info_url: '',
    twitch_channel: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('moonrise_token');
    if (!token) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      try {
        const [settingsRes, tournamentsRes] = await Promise.all([
          client.get('/homepage/settings'),
          client.get('/tournaments'),
        ]);
        const s = settingsRes.data;
        setSettings({
          tournament_id: s.tournament_id || '',
          title: s.title || '',
          date_text: s.date_text || '',
          description: s.description || '',
          logo_url: s.logo_url || '',
          hero_image_url: s.hero_image_url || '',
          registration_text: s.registration_text || '',
          registration_url: s.registration_url || '',
          info_text: s.info_text || '',
          info_url: s.info_url || '',
          twitch_channel: s.twitch_channel || '',
        });
        setTournaments(tournamentsRes.data || []);
      } catch (err) {
        setError('Failed to load data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings(prev => ({ ...prev, [name]: value }));
    setSuccess(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess(false);

    try {
      const token = localStorage.getItem('moonrise_token');
      await client.put('/homepage/settings', settings, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save.');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="ahs-loading">Loading...</div>;

  return (
    <div className="ahs-page">
      <h1 className="ahs-title" style={{ fontFamily: 'Palui', color: 'var(--accent-light)' }}>
        Настройки главной страницы
      </h1>

      {error && <div className="ahs-error">{error}</div>}
      {success && <div className="ahs-success">✓ Настройки сохранены!</div>}

      <form onSubmit={handleSubmit} className="ahs-form">
        {/* Продвигаемый турнир */}
        <div className="ahs-section">
          <h3 className="ahs-section-title">Продвигаемый турнир</h3>
          <div className="ahs-field">
            <label htmlFor="tournament_id">Турнир для продвижения</label>
            <select
              id="tournament_id"
              name="tournament_id"
              value={settings.tournament_id}
              onChange={handleChange}
              className="ahs-input"
            >
              <option value="">— Не выбран —</option>
              {tournaments.map(t => (
                <option key={t.id} value={t.id}>{t.title}</option>
              ))}
            </select>
            <p className="ahs-hint">Кнопки будут вести на этот турнир. Если не выбран — используются URL ниже.</p>
          </div>
        </div>

        {/* Текстовый контент */}
        <div className="ahs-section">
          <h3 className="ahs-section-title">Контент</h3>
          <div className="ahs-grid-2">
            <div className="ahs-field">
              <label htmlFor="title">Заголовок блока</label>
              <input id="title" name="title" value={settings.title} onChange={handleChange} className="ahs-input" placeholder="UPCOMING TOURNAMENT" />
            </div>
            <div className="ahs-field">
              <label htmlFor="date_text">Дата (текст)</label>
              <input id="date_text" name="date_text" value={settings.date_text} onChange={handleChange} className="ahs-input" placeholder="08 - 09 MARCH" />
            </div>
          </div>
          <div className="ahs-field">
            <label htmlFor="description">Короткое описание</label>
            <textarea id="description" name="description" value={settings.description} onChange={handleChange} rows="3" className="ahs-input" placeholder="Краткое описание турнира..." />
          </div>
        </div>

        {/* Изображения */}
        <div className="ahs-section">
          <h3 className="ahs-section-title">Изображения</h3>
          <div className="ahs-grid-2">
            <div className="ahs-field">
              <label htmlFor="logo_url">Логотип (URL)</label>
              <input id="logo_url" name="logo_url" value={settings.logo_url} onChange={handleChange} className="ahs-input" placeholder="/assets/images/..." />
            </div>
            <div className="ahs-field">
              <label htmlFor="hero_image_url">Главное изображение (URL)</label>
              <input id="hero_image_url" name="hero_image_url" value={settings.hero_image_url} onChange={handleChange} className="ahs-input" placeholder="/assets/images/..." />
            </div>
          </div>
        </div>

        {/* Кнопки */}
        <div className="ahs-section">
          <h3 className="ahs-section-title">Кнопки</h3>
          <div className="ahs-grid-2">
            <div className="ahs-field">
              <label htmlFor="registration_text">Текст кнопки регистрации</label>
              <input id="registration_text" name="registration_text" value={settings.registration_text} onChange={handleChange} className="ahs-input" placeholder="REGISTRATION" />
            </div>
            <div className="ahs-field">
              <label htmlFor="registration_url">URL кнопки регистрации</label>
              <input id="registration_url" name="registration_url" value={settings.registration_url} onChange={handleChange} className="ahs-input" placeholder="#" />
            </div>
          </div>
          <div className="ahs-grid-2">
            <div className="ahs-field">
              <label htmlFor="info_text">Текст кнопки "Инфо"</label>
              <input id="info_text" name="info_text" value={settings.info_text} onChange={handleChange} className="ahs-input" placeholder="INFO" />
            </div>
            <div className="ahs-field">
              <label htmlFor="info_url">URL кнопки "Инфо"</label>
              <input id="info_url" name="info_url" value={settings.info_url} onChange={handleChange} className="ahs-input" placeholder="#" />
            </div>
          </div>
        </div>

        {/* Трансляция */}
        <div className="ahs-section">
          <h3 className="ahs-section-title">Трансляция</h3>
          <div className="ahs-field">
            <label htmlFor="twitch_channel">Twitch канал</label>
            <input id="twitch_channel" name="twitch_channel" value={settings.twitch_channel} onChange={handleChange} className="ahs-input" placeholder="shroud" />
            <p className="ahs-hint">Embed появится на главной странице когда турнир в статусе "ongoing".</p>
          </div>
        </div>

        {/* Кнопки */}
        <div className="ahs-actions">
          <button type="button" className="ahs-btn ahs-btn-secondary" onClick={() => navigate('/admin/tournaments')}>Назад</button>
          <button type="submit" disabled={saving} className="ahs-btn ahs-btn-primary">
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </form>
    </div>
  );
}
