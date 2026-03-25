import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function UpcomingTournamentSection() {
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    fetch('/api/homepage/settings')
      .then(r => r.json())
      .then(data => setSettings(data))
      .catch(() => {})
  }, [])

  // Пока загружается — показываем захардкоженный вариант
  const s = settings || {
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

  const regLink = s.tournament_id ? `/tournaments/${s.tournament_id}` : s.registration_url
  const infoLink = s.tournament_id ? `/tournaments/${s.tournament_id}` : s.info_url

  return (
    <section className="tournament-section">
      <div className="tournament-card reveal">

        <div className="tournament-top reveal reveal-delay-1">
          <div className="tournament-dot"></div>
          <span className="tournament-label">{s.title}</span>
          <div className="tournament-line"></div>
          <span className="tournament-date">{s.date_text}</span>
        </div>

        <div className="tournament-grid">
          <div className="tournament-left">
            {s.logo_url && (
              <img
                className="tournament-mix-logo reveal reveal-delay-2"
                src={s.logo_url}
                alt="Tournament Logo"
              />
            )}
            <p className="tournament-description reveal reveal-delay-3">
              {s.description}
            </p>
            <div className="tournament-actions reveal reveal-delay-4">
              <Link to={regLink} className="cyber-button-secondary">
                {s.registration_text}
              </Link>
              <Link to={infoLink} className="cyber-button-outline">
                {s.info_text}
              </Link>
            </div>
          </div>

          <div className="tournament-right reveal reveal-delay-2">
            {s.hero_image_url && (
              <img src={s.hero_image_url} alt="Tournament Hero" />
            )}
          </div>
        </div>

      </div>
    </section>
  )
}