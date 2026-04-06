import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'

const DEFAULT_SETTINGS = {
  title: 'UPCOMING TOURNAMENT',
  date_text: '08 - 09 MARCH',
  description: 'ТУРНИР, В КОТОРОМ КОМАНДЫ ФОРМИРУЮТСЯ С ПОМОЩЬЮ ИНСТРУМЕНТОВ ДЛЯ БАЛАНСА КОМАНД. ОСНОВНОЙ ПРИНЦИП ФОРМИРОВАНИЯ КОМАНД — БАЛАНС СРЕДНЕГО РЕЙТИНГА МЕЖДУ ВСЕМИ КОМАНДАМИ.',
  logo_url: '/assets/images/tournament-mix-logo.png',
  hero_image_url: '/assets/images/tournament-hero.png',
  registration_text: 'REGISTRATION',
  registration_url: '#',
  info_text: 'INFO',
  info_url: '#',
  tournament_id: null,
}

export default function UpcomingTournamentSection() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)

  useEffect(() => {
    client.get('/homepage/settings')
      .then(r => {
        console.log('📋 Homepage settings raw:', r.data)
        setSettings(prev => {
          const merged = { ...prev }
          Object.keys(r.data).forEach(key => {
            if (r.data[key] !== null && r.data[key] !== undefined && r.data[key] !== '') {
              merged[key] = r.data[key]
            }
          })
          console.log('📋 Merged settings:', merged)
          return merged
        })
      })
      .catch(err => {
        console.warn('⚠️ Homepage settings failed, using defaults:', err.response?.status)
      })
  }, [])

  const regLink = settings.tournament_id
    ? `/tournaments/${settings.tournament_id}`
    : settings.registration_url || '#'

  const infoLink = settings.tournament_id
    ? `/tournaments/${settings.tournament_id}`
    : settings.info_url || '#'

  return (
    <section className="tournament-section">
      <div className="tournament-card reveal">

        {/* TOP BAR */}
        <div className="tournament-top reveal reveal-delay-1">
          <div className="tournament-dot" />
          <span className="tournament-label">{settings.title}</span>
          <div className="tournament-line" />
          <span className="tournament-date">{settings.date_text}</span>
        </div>

        {/* GRID: левая колонка + правая с персонажем */}
        <div className="tournament-grid">

          {/* ЛЕВАЯ */}
          <div className="tournament-left">
            <img
              className="tournament-mix-logo reveal reveal-delay-2"
              src={settings.logo_url}
              alt="MoonRise MIX"
            />
            <p className="tournament-description reveal reveal-delay-3">
              {settings.description}
            </p>
            <div className="tournament-actions reveal reveal-delay-4">
              <Link to={regLink} className="cyber-button-secondary">
                {settings.registration_text || 'REGISTRATION'}
              </Link>
              <Link to={infoLink} className="cyber-button-outline">
                {settings.info_text || 'INFO'}
              </Link>
            </div>
          </div>

          {/* ПРАВАЯ — персонаж вровень с низом карточки */}
          <div className="tournament-right reveal reveal-delay-2">
            <img
              src={settings.hero_image_url}
              alt="Tournament Hero"
            />
          </div>

        </div>
      </div>
    </section>
  )
}