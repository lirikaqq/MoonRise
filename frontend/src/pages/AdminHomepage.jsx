import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import './AdminHomepage.css'

export default function AdminHomepage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [tournaments, setTournaments] = useState([])

  // Проверка что пользователь админ
  useEffect(() => {
    if (!user) return
    if (user.role !== 'admin') {
      navigate('/')
    }
  }, [user, navigate])

  // Загружаем настройки и список турниров
  useEffect(() => {
    const token = localStorage.getItem('moonrise_token')

    Promise.all([
      fetch('/api/homepage/settings').then(r => r.json()),
      fetch('/api/tournaments?limit=50').then(r => r.json())
    ])
      .then(([s, t]) => {
        setSettings(s)
        setTournaments(t)
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)

    try {
      const token = localStorage.getItem('moonrise_token')
      const res = await fetch('/api/homepage/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(settings)
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to save')
      }

      const updated = await res.json()
      setSettings(updated)
      setMessage({ type: 'success', text: 'SETTINGS SAVED SUCCESSFULLY!' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message.toUpperCase() })
    } finally {
      setSaving(false)
    }
  }

  if (!user || user.role !== 'admin') {
    return (
      <div className="admin-page">
        <Header />
        <main className="admin-main">
          <div className="admin-denied">ACCESS DENIED</div>
        </main>
        <Footer />
      </div>
    )
  }

  if (loading || !settings) {
    return (
      <div className="admin-page">
        <Header />
        <main className="admin-main">
          <div className="admin-loading">LOADING...</div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="admin-page">
      <Header />

      <main className="admin-main">
        <div className="admin-container">

          <h1 className="admin-title">
            <span className="admin-title-dot">•</span>
            ADMIN — HOMEPAGE SETTINGS
          </h1>
          <div className="admin-title-bar"></div>

          <div className="admin-layout">

            {/* ФОРМА */}
            <div className="admin-form">

              {/* Привязка к турниру */}
              <div className="admin-field">
                <label>LINKED TOURNAMENT</label>
                <select
                  value={settings.tournament_id || ''}
                  onChange={e => handleChange('tournament_id', e.target.value ? parseInt(e.target.value) : null)}
                >
                  <option value="">— NOT LINKED —</option>
                  {tournaments.map(t => (
                    <option key={t.id} value={t.id}>
                      {t.title} ({t.format.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              {/* Заголовок */}
              <div className="admin-field">
                <label>SECTION TITLE</label>
                <input
                  type="text"
                  value={settings.title}
                  onChange={e => handleChange('title', e.target.value)}
                />
              </div>

              {/* Дата */}
              <div className="admin-field">
                <label>DATE TEXT</label>
                <input
                  type="text"
                  value={settings.date_text}
                  onChange={e => handleChange('date_text', e.target.value)}
                  placeholder="08 - 09 MARCH"
                />
              </div>

              {/* Описание */}
              <div className="admin-field">
                <label>DESCRIPTION</label>
                <textarea
                  value={settings.description}
                  onChange={e => handleChange('description', e.target.value)}
                  rows={4}
                />
              </div>

              {/* Логотип */}
              <div className="admin-field">
                <label>LOGO IMAGE URL</label>
                <input
                  type="text"
                  value={settings.logo_url || ''}
                  onChange={e => handleChange('logo_url', e.target.value)}
                  placeholder="/assets/images/tournament-mix-logo.png"
                />
              </div>

              {/* Hero */}
              <div className="admin-field">
                <label>HERO IMAGE URL</label>
                <input
                  type="text"
                  value={settings.hero_image_url || ''}
                  onChange={e => handleChange('hero_image_url', e.target.value)}
                  placeholder="/assets/images/tournament-hero.png"
                />
              </div>

              {/* Кнопка регистрации */}
              <div className="admin-row">
                <div className="admin-field">
                  <label>REGISTRATION BUTTON TEXT</label>
                  <input
                    type="text"
                    value={settings.registration_text}
                    onChange={e => handleChange('registration_text', e.target.value)}
                  />
                </div>
                <div className="admin-field">
                  <label>REGISTRATION URL</label>
                  <input
                    type="text"
                    value={settings.registration_url}
                    onChange={e => handleChange('registration_url', e.target.value)}
                    placeholder="/tournaments/1"
                  />
                </div>
              </div>

              {/* Кнопка INFO */}
              <div className="admin-row">
                <div className="admin-field">
                  <label>INFO BUTTON TEXT</label>
                  <input
                    type="text"
                    value={settings.info_text}
                    onChange={e => handleChange('info_text', e.target.value)}
                  />
                </div>
                <div className="admin-field">
                  <label>INFO URL</label>
                  <input
                    type="text"
                    value={settings.info_url}
                    onChange={e => handleChange('info_url', e.target.value)}
                    placeholder="/tournaments/1"
                  />
                </div>
              </div>

              {/* SAVE */}
              <button
                className="admin-save-btn"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'SAVING...' : 'SAVE CHANGES'}
              </button>

              {message && (
                <div className={`admin-message admin-message-${message.type}`}>
                  {message.type === 'success' ? '✓' : '✕'} {message.text}
                </div>
              )}

            </div>

            {/* ПРЕВЬЮ */}
            <div className="admin-preview">
              <div className="admin-preview-title">PREVIEW</div>
              <div className="admin-preview-card">

                <div className="tournament-top">
                  <div className="tournament-dot"></div>
                  <span className="tournament-label">{settings.title}</span>
                  <div className="tournament-line"></div>
                  <span className="tournament-date">{settings.date_text}</span>
                </div>

                <div className="admin-preview-content">
                  {settings.logo_url && (
                    <img src={settings.logo_url} alt="Logo" className="admin-preview-logo" />
                  )}
                  <p className="admin-preview-desc">{settings.description}</p>
                  <div className="admin-preview-buttons">
                    <span className="admin-preview-btn-reg">{settings.registration_text}</span>
                    <span className="admin-preview-btn-info">{settings.info_text}</span>
                  </div>
                </div>

                {settings.hero_image_url && (
                  <img src={settings.hero_image_url} alt="Hero" className="admin-preview-hero" />
                )}

              </div>
            </div>

          </div>

        </div>
      </main>

      <Footer />
    </div>
  )
}