import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { tournamentsApi } from '../api/tournaments'
import { useAuth } from '../context/AuthContext' // ← ДОБАВИЛИ
import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import './Tournaments.css'

function formatDate(start, end) {
  if (!start || !end) return 'TBA'
  const s = new Date(start)
  const e = new Date(end)
  const months = [
    'JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE',
    'JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'
  ]
  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()) {
    if (s.getDate() === e.getDate()) {
      return `${s.getDate()} ${months[s.getMonth()]}, ${s.getFullYear()}`
    }
    return `${s.getDate()}-${e.getDate()} ${months[s.getMonth()]}, ${s.getFullYear()}`
  }
  return `${s.getDate()} ${months[s.getMonth()]} - ${e.getDate()} ${months[e.getMonth()]}, ${s.getFullYear()}`
}

function getFormatIcon(format) {
  const map = {
    mix: '/assets/icons/mix_icon.svg',
    draft: '/assets/icons/cup.svg',
    start: '/assets/icons/cup.svg',
    other: '/assets/icons/star.svg',
  }
  return map[format] || '/assets/icons/star.svg'
}

const COVER_MAP = [
  { keywords: ['mix #3', 'mix vol.3', 'mix vol 3'], cover: '/assets/images/tournaments/moonrise_mix_3.webp' },
  { keywords: ['mix #2', 'mix vol.2', 'mix vol 2'], cover: '/assets/images/tournaments/moonrise_mix_2.webp' },
  { keywords: ['mix #1', 'mix vol.1', 'mix vol 1'], cover: '/assets/images/tournaments/moonrise_mix_1.webp' },
  { keywords: ['mix'],                               cover: '/assets/images/tournaments/moonrise_mix_1.webp' },
  { keywords: ['valentine', '2x2', '2х2'],           cover: '/assets/images/tournaments/valentines_cup.webp' },
  { keywords: ['draft'],                              cover: '/assets/images/tournaments/moonrise_draft.webp' },
  { keywords: ['lucio', 'wave'],                      cover: '/assets/images/tournaments/lucio_wave_clash.webp' },
  { keywords: ['nomercy', 'no mercy'],                cover: '/assets/images/tournaments/nomercy_tournament.webp' },
]

function getCoverUrl(tournament) {
  if (tournament.cover_url) return tournament.cover_url
  const title = (tournament.title || '').toLowerCase()
  for (const entry of COVER_MAP) {
    if (entry.keywords.some(kw => title.includes(kw))) {
      return entry.cover
    }
  }
  const formatFallback = {
    mix: '/assets/images/tournaments/moonrise_mix_1.webp',
    draft: '/assets/images/tournaments/moonrise_draft.webp',
  }
  if (tournament.format && formatFallback[tournament.format]) {
    return formatFallback[tournament.format]
  }
  return null
}

// ✅ ДОБАВИЛИ ЛОГИКУ СТАТУСОВ ЗАЯВОК
function TournamentButton({ status, id, myAppStatus }) {
  if (status === 'completed' || status === 'cancelled') {
    return <Link to={`/tournaments/${id}`} className="t-card-btn t-btn-view font-palui">VIEW DETAILS</Link>
  }
  
  if (myAppStatus === 'registered') {
    return <Link to={`/tournaments/${id}`} className="t-card-btn t-btn-view font-palui" style={{ backgroundColor: '#13ad91', color: '#fff', borderColor: '#13ad91' }}>✓ ОДОБРЕНЫ</Link>
  }
  
  if (myAppStatus === 'pending') {
    return <Link to={`/tournaments/${id}`} className="t-card-btn t-btn-view font-palui" style={{ backgroundColor: '#2a2a3e', color: '#a0a0a0', borderColor: '#404050' }}>⏳ ОЖИДАНИЕ</Link>
  }
  
  if (status === 'registration') {
    return <Link to={`/tournaments/${id}`} className="t-card-btn t-btn-registration font-palui">REGISTRATION</Link>
  }
  
  if (status === 'checkin') {
    return <Link to={`/tournaments/${id}`} className="t-card-btn t-btn-checkin font-palui">CHECK-IN</Link>
  }
  
  return <Link to={`/tournaments/${id}`} className="t-card-btn t-btn-view font-palui">VIEW DETAILS</Link>
}

// ✅ ПЕРЕДАЕМ myAppStatus В КНОПКУ
function TournamentCard({ tournament, myAppStatus }) {
  const isOpen = tournament.status === 'registration' || tournament.status === 'checkin'
  const coverUrl = getCoverUrl(tournament)

  return (
    <div className={`t-card ${isOpen ? 't-card-open' : ''}`}>
      <div className="t-card-cover">
        {coverUrl ? (
          <img src={coverUrl} alt={tournament.title} />
        ) : (
          <div className="t-card-cover-empty"></div>
        )}
        {isOpen && <div className="t-card-badge font-ponter">OPEN</div>}
      </div>

      <div className="t-card-content">
        <h3 className="t-card-title font-digits">
          <img src={getFormatIcon(tournament.format)} alt="" className="t-card-format-icon" />
          {tournament.title ? tournament.title.toUpperCase() : 'TOURNAMENT'}
        </h3>

        <div className="t-card-meta">
          <span className="t-card-meta-item font-ponter">
            <img src="/assets/icons/calend.svg" alt="" className="t-card-meta-svg" />
            {formatDate(tournament.start_date, tournament.end_date)}
          </span>
          <span className="t-card-meta-item font-ponter">
            <img src="/assets/icons/people.svg" alt="" className="t-card-meta-svg" />
            {tournament.participants_count || 0}
          </span>
        </div>

        <TournamentButton status={tournament.status} id={tournament.id} myAppStatus={myAppStatus} />
      </div>
    </div>
  )
}

const FILTERS = [
  { key: 'all', label: 'ALL' },
  { key: 'mix', label: 'MIX' },
  { key: 'start', label: 'EVENT' },
  { key: 'draft', label: 'DRAFT' },
]

export default function Tournaments() {
  const { user } = useAuth() // ← ДОБАВИЛИ
  const [tournaments, setTournaments] = useState([])
  const [myApps, setMyApps] = useState({}) // ← ДОБАВИЛИ (хранит статусы заявок)
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  // ЗАГРУЗКА ТУРНИРОВ
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await tournamentsApi.getAll({
          format: activeFilter === 'all' ? null : activeFilter,
          search: search || null,
        })
        setTournaments(Array.isArray(data) ? data : [])
      } catch (err) {
        console.error('Failed to load tournaments:', err)
        setTournaments([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [activeFilter, search])

  // ✅ ЗАГРУЗКА СТАТУСОВ ЗАЯВОК ТЕКУЩЕГО ЮЗЕРА
  useEffect(() => {
    if (user) {
      tournamentsApi.getMyAllApplications()
        .then(apps => {
          const appsMap = {}
          // apps = [{tournament_id: 1, status: 'pending'}, ...]
          apps.forEach(app => {
            appsMap[app.tournament_id] = app.status
          })
          setMyApps(appsMap)
        })
        .catch(console.error)
    } else {
      setMyApps({})
    }
  }, [user])

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 400)
    return () => clearTimeout(timer)
  }, [searchInput])

  return (
    <div className="t-page">
      <Header />

      <main className="t-main">
        <div className="t-container">

          <div className="t-header">
            <h1 className="t-title font-palui">
              <span className="t-title-dot">•</span>
              ИНФОРМАЦИЯ О ТУРНИРАХ
            </h1>
            <p className="t-subtitle font-ponter">
              <span className="t-subtitle-bar"></span>
              ПРОСМОТР ИНФОРМАЦИИ О ТЕКУЩИХ И ПРОШЕДШИХ ТУРНИРАХ
            </p>
          </div>

          <div className="t-controls">
            <div className="t-search">
              <img src="/assets/icons/lupa.svg" alt="" className="t-search-icon" />
              <input
                type="text"
                placeholder="ПОИСК ТУРНИРА..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="t-search-input font-ponter"
              />
            </div>

            <div className="t-filters">
              {FILTERS.map(f => (
                <button
                  key={f.key}
                  className={`t-filter-btn font-ponter ${activeFilter === f.key ? 't-filter-active' : ''}`}
                  onClick={() => setActiveFilter(f.key)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="t-loading">
              <div className="t-loading-spinner"></div>
              <span className="font-palui">LOADING...</span>
            </div>
          ) : tournaments.length === 0 ? (
            <div className="t-empty font-palui">
              <p>ТУРНИРЫ НЕ НАЙДЕНЫ</p>
            </div>
          ) : (
            <div className="t-grid">
              {tournaments.map(t => (
                <TournamentCard key={t.id} tournament={t} myAppStatus={myApps[t.id]} />
              ))}
            </div>
          )}

        </div>
      </main>

      <Footer />
    </div>
  )
}