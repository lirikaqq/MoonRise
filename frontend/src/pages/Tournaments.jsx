import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { tournamentsApi } from '../api/tournaments'
import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import './Tournaments.css'

// Форматируем дату: "7-8 MARCH, 2026"
function formatDate(start, end) {
  const s = new Date(start)
  const e = new Date(end)

  const months = [
    'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'
  ]

  const month = months[s.getMonth()]
  const year = s.getFullYear()

  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()) {
    return `${s.getDate()}-${e.getDate()} ${month}, ${year}`
  }

  return `${s.getDate()} ${months[s.getMonth()]} - ${e.getDate()} ${months[e.getMonth()]}, ${year}`
}

// Иконка формата турнира
function FormatIcon({ format }) {
  const icons = {
    mix: '⚡',
    draft: '🎯',
    start: '🏆',
    other: '⭐',
  }
  return <span className="tournament-format-icon">{icons[format] || '⭐'}</span>
}

// Кнопка действия в зависимости от статуса
function TournamentButton({ status, id }) {
  if (status === 'registration') {
    return (
      <Link to={`/tournaments/${id}`} className="tournament-card-btn btn-registration">
        REGISTRATION
      </Link>
    )
  }
  if (status === 'checkin') {
    return (
      <Link to={`/tournaments/${id}`} className="tournament-card-btn btn-checkin">
        CHECK-IN
      </Link>
    )
  }
  return (
    <Link to={`/tournaments/${id}`} className="tournament-card-btn btn-view">
      VIEW DETAILS
    </Link>
  )
}

// Карточка турнира
function TournamentCard({ tournament }) {
  const isOpen = tournament.status === 'registration' || tournament.status === 'checkin'

  return (
    <div className={`tournament-card-item ${isOpen ? 'card-open' : ''}`}>
      {/* Обложка */}
      <div className="tournament-card-cover">
        {tournament.cover_url ? (
          <img src={tournament.cover_url} alt={tournament.title} />
        ) : (
          <div className="tournament-card-cover-placeholder">
            <img src="/assets/images/logo.svg" alt="MoonRise" />
          </div>
        )}
        {isOpen && (
          <div className="tournament-card-badge">OPEN</div>
        )}
      </div>

      {/* Контент */}
      <div className="tournament-card-content">
        {/* Название */}
        <h3 className="tournament-card-title">
          <FormatIcon format={tournament.format} />
          {tournament.title.toUpperCase()}
        </h3>

        {/* Дата и участники */}
        <div className="tournament-card-meta">
          <span className="tournament-card-date">
            📅 {formatDate(tournament.start_date, tournament.end_date)}
          </span>
          <span className="tournament-card-participants">
            👥 {tournament.participants_count}
          </span>
        </div>

        {/* Кнопка */}
        <TournamentButton status={tournament.status} id={tournament.id} />
      </div>
    </div>
  )
}

// Фильтр
const FILTERS = [
  { key: 'all', label: 'ALL' },
  { key: 'mix', label: 'MIX' },
  { key: 'start', label: 'START' },
  { key: 'draft', label: 'DRAFT' },
]

export default function Tournaments() {
  const [tournaments, setTournaments] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  // Загружаем турниры
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await tournamentsApi.getAll({
          format: activeFilter === 'all' ? null : activeFilter,
          search: search || null,
        })
        setTournaments(data)
      } catch (err) {
        console.error('Failed to load tournaments:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [activeFilter, search])

  // Поиск с задержкой
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput)
    }, 400)
    return () => clearTimeout(timer)
  }, [searchInput])

  return (
    <div className="tournaments-page">
      <Header />

      <main className="tournaments-main">
        <div className="tournaments-container">

          {/* Заголовок */}
          <div className="tournaments-header">
            <h1 className="tournaments-title">
              <span className="tournaments-title-dot">•</span>
              ИНФОРМАЦИЯ О ТУРНИРАХ
            </h1>
            <div className="tournaments-title-bar"></div>
            <p className="tournaments-subtitle">
              ПРОСМОТР ИНФОРМАЦИИ О ТЕКУЩИХ И ПРОШЕДШИХ ТУРНИРАХ
            </p>
          </div>

          {/* Поиск и фильтры */}
          <div className="tournaments-controls">
            {/* Поиск */}
            <div className="tournaments-search">
              <span className="tournaments-search-icon">🔍</span>
              <input
                type="text"
                placeholder="ПОИСК ТУРНИРА..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="tournaments-search-input"
              />
            </div>

            {/* Фильтры */}
            <div className="tournaments-filters">
              {FILTERS.map(f => (
                <button
                  key={f.key}
                  className={`tournaments-filter-btn ${activeFilter === f.key ? 'active' : ''}`}
                  onClick={() => setActiveFilter(f.key)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Список турниров */}
          {loading ? (
            <div className="tournaments-loading">
              <div className="tournaments-loading-spinner"></div>
              <span>LOADING...</span>
            </div>
          ) : tournaments.length === 0 ? (
            <div className="tournaments-empty">
              <p>ТУРНИРЫ НЕ НАЙДЕНЫ</p>
            </div>
          ) : (
            <div className="tournaments-grid">
              {tournaments.map(t => (
                <TournamentCard key={t.id} tournament={t} />
              ))}
            </div>
          )}

        </div>
      </main>

      <Footer />
    </div>
  )
}