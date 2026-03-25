import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { tournamentsApi } from '../api/tournaments'
import { useAuth } from '../context/AuthContext'
import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import './TournamentDetail.css'

function formatDate(start, end) {
  const s = new Date(start)
  const e = new Date(end)
  const months = [
    'JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE',
    'JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'
  ]
  const month = months[s.getMonth()]
  const year = s.getFullYear()
  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()) {
    return `${s.getDate()}-${e.getDate()} ${month}, ${year}`
  }
  return `${s.getDate()} ${months[s.getMonth()]} — ${e.getDate()} ${months[e.getMonth()]}, ${year}`
}

function formatDateTime(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  const months = [
    'JAN','FEB','MAR','APR','MAY','JUN',
    'JUL','AUG','SEP','OCT','NOV','DEC'
  ]
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function StatusBadge({ status }) {
  const labels = {
    upcoming:     { text: 'UPCOMING',     cls: 'badge-upcoming' },
    registration: { text: 'OPEN REG',     cls: 'badge-registration' },
    checkin:      { text: 'CHECK-IN',     cls: 'badge-checkin' },
    ongoing:      { text: 'LIVE',         cls: 'badge-ongoing' },
    completed:    { text: 'COMPLETED',    cls: 'badge-completed' },
    cancelled:    { text: 'CANCELLED',    cls: 'badge-cancelled' },
  }
  const s = labels[status] || { text: status.toUpperCase(), cls: '' }
  return <span className={`td-status-badge ${s.cls}`}>{s.text}</span>
}

function FormatBadge({ format }) {
  const map = {
    mix:   { icon: '⚡', label: 'MIX' },
    draft: { icon: '🎯', label: 'DRAFT' },
    start: { icon: '🏆', label: 'START' },
    other: { icon: '◈',  label: 'OTHER' },
  }
  const f = map[format] || { icon: '◈', label: format?.toUpperCase() }
  return (
    <span className="td-format-badge">
      {f.icon} {f.label}
    </span>
  )
}

function ActionButton({ tournament, user, myStatus, onAction, loading }) {
  const { status } = tournament

  if (status === 'completed' || status === 'cancelled') {
    return <div className="td-action-ended">TOURNAMENT {status.toUpperCase()}</div>
  }

  if (status === 'ongoing') {
    return <div className="td-action-live">🔴 TOURNAMENT IN PROGRESS</div>
  }

  if (!user) {
    return (
      <button className="td-action-btn btn-login" onClick={onAction}>
        <img src="/assets/icons/discord.svg" alt="" />
        LOG IN TO REGISTER
      </button>
    )
  }

  // Уже зарегистрирован
  if (myStatus === 'registered') {
    if (status === 'checkin') {
      return (
        <button className="td-action-btn btn-checkin" onClick={onAction} disabled={loading}>
          {loading ? 'LOADING...' : '✓ CHECK-IN NOW'}
        </button>
      )
    }
    return <div className="td-action-upcoming">✓ YOU ARE REGISTERED</div>
  }

  // Уже чекнулся
  if (myStatus === 'checkedin') {
    return <div className="td-action-upcoming">✓ CHECK-IN CONFIRMED</div>
  }

  if (status === 'registration') {
    return (
      <button className="td-action-btn btn-register" onClick={onAction} disabled={loading}>
        {loading ? 'LOADING...' : 'REGISTER'}
      </button>
    )
  }

  if (status === 'checkin') {
    return <div className="td-action-upcoming">REGISTRATION IS CLOSED</div>
  }

  return <div className="td-action-upcoming">REGISTRATION NOT OPEN YET</div>
}

export default function TournamentDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [tournament, setTournament] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [myStatus, setMyStatus] = useState(null)

  // Загружаем турнир
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await tournamentsApi.getById(id)
        setTournament(data)
      } catch (err) {
        console.error('Failed to load tournament:', err)
        setMessage({ type: 'error', text: 'TOURNAMENT NOT FOUND' })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Загружаем статус участника
  useEffect(() => {
    if (!user || !tournament) return
    const token = localStorage.getItem('moonrise_token')
    if (!token) return

    fetch(`/api/tournaments/${id}/my-status`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setMyStatus(data.registered ? data.status : null))
      .catch(() => {})
  }, [user, tournament, id])

  const handleAction = async () => {
    if (!user) {
      window.location.href = '/api/auth/discord'
      return
    }

    setActionLoading(true)
    setMessage(null)

    try {
      const token = localStorage.getItem('moonrise_token')

      if (myStatus === 'registered' && tournament.status === 'checkin') {
        await tournamentsApi.checkin(id, token)
        setMessage({ type: 'success', text: 'CHECK-IN CONFIRMED!' })
        setMyStatus('checkedin')
      } else if (!myStatus && tournament.status === 'registration') {
        await tournamentsApi.register(id, token)
        setMessage({ type: 'success', text: 'YOU HAVE SUCCESSFULLY REGISTERED!' })
        setMyStatus('registered')
      }

      const updated = await tournamentsApi.getById(id)
      setTournament(updated)
    } catch (err) {
      const detail = err?.response?.data?.detail || 'SOMETHING WENT WRONG'
      setMessage({ type: 'error', text: detail.toUpperCase() })
    } finally {
      setActionLoading(false)
    }
  }

  const fillPercent = tournament
    ? Math.min(100, Math.round((tournament.participants_count / (tournament.max_participants || 100)) * 100))
    : 0

  if (loading) {
    return (
      <div className="td-page">
        <Header />
        <main className="td-main">
          <div className="td-loading">
            <div className="td-loading-spinner"></div>
            <span>LOADING...</span>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  if (!tournament) {
    return (
      <div className="td-page">
        <Header />
        <main className="td-main">
          <div className="td-not-found">
            <p>TOURNAMENT NOT FOUND</p>
            <Link to="/tournaments" className="td-back-btn">← BACK TO TOURNAMENTS</Link>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="td-page">
      <Header />

      <main className="td-main">
        <div className="td-container">

          <div className="td-breadcrumb">
            <Link to="/tournaments">TOURNAMENTS</Link>
            <span className="td-breadcrumb-sep">›</span>
            <span>{tournament.title.toUpperCase()}</span>
          </div>

          <div className="td-layout">

            {/* ЛЕВАЯ КОЛОНКА */}
            <div className="td-sidebar">

              <div className="td-cover">
                {tournament.cover_url ? (
                  <img src={tournament.cover_url} alt={tournament.title} />
                ) : (
                  <div className="td-cover-placeholder">
                    <img src="/assets/images/logo.svg" alt="MoonRise" />
                  </div>
                )}
                <StatusBadge status={tournament.status} />
              </div>

              <div className="td-participants-block">
                <div className="td-participants-header">
                  <span className="td-participants-label">PARTICIPANTS</span>
                  <span className="td-participants-count">
                    {tournament.participants_count}
                    <span className="td-participants-max">/ {tournament.max_participants}</span>
                  </span>
                </div>
                <div className="td-progress-bar">
                  <div className="td-progress-fill" style={{ width: `${fillPercent}%` }}></div>
                </div>
                <span className="td-progress-percent">{fillPercent}% FILLED</span>
              </div>

              <ActionButton
                tournament={tournament}
                user={user}
                myStatus={myStatus}
                onAction={handleAction}
                loading={actionLoading}
              />

              {message && (
                <div className={`td-message td-message-${message.type}`}>
                  {message.type === 'success' ? '✓' : '✕'} {message.text}
                </div>
              )}

            </div>

            {/* ПРАВАЯ КОЛОНКА */}
            <div className="td-content">

              <div className="td-title-block">
                <div className="td-title-row">
                  <FormatBadge format={tournament.format} />
                  <StatusBadge status={tournament.status} />
                </div>
                <h1 className="td-title">{tournament.title.toUpperCase()}</h1>
                <div className="td-title-bar"></div>
              </div>

              {tournament.description && (
                <div className="td-section">
                  <h2 className="td-section-title">
                    <span className="td-section-dot">•</span>
                    ABOUT TOURNAMENT
                  </h2>
                  <p className="td-description">{tournament.description}</p>
                </div>
              )}

              <div className="td-section">
                <h2 className="td-section-title">
                  <span className="td-section-dot">•</span>
                  SCHEDULE
                </h2>
                <div className="td-schedule">
                  <div className="td-schedule-row">
                    <span className="td-schedule-label">📅 TOURNAMENT DATES</span>
                    <span className="td-schedule-value">
                      {formatDate(tournament.start_date, tournament.end_date)}
                    </span>
                  </div>
                  {tournament.registration_open && (
                    <div className="td-schedule-row">
                      <span className="td-schedule-label">📝 REGISTRATION OPENS</span>
                      <span className="td-schedule-value">
                        {formatDateTime(tournament.registration_open)}
                      </span>
                    </div>
                  )}
                  {tournament.registration_close && (
                    <div className="td-schedule-row">
                      <span className="td-schedule-label">🔒 REGISTRATION CLOSES</span>
                      <span className="td-schedule-value">
                        {formatDateTime(tournament.registration_close)}
                      </span>
                    </div>
                  )}
                  {tournament.checkin_open && (
                    <div className="td-schedule-row">
                      <span className="td-schedule-label">✅ CHECK-IN OPENS</span>
                      <span className="td-schedule-value">
                        {formatDateTime(tournament.checkin_open)}
                      </span>
                    </div>
                  )}
                  {tournament.checkin_close && (
                    <div className="td-schedule-row">
                      <span className="td-schedule-label">⏰ CHECK-IN CLOSES</span>
                      <span className="td-schedule-value">
                        {formatDateTime(tournament.checkin_close)}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="td-section">
                <h2 className="td-section-title">
                  <span className="td-section-dot">•</span>
                  TOURNAMENT INFO
                </h2>
                <div className="td-info-grid">
                  <div className="td-info-card">
                    <span className="td-info-label">FORMAT</span>
                    <span className="td-info-value">
                      <FormatBadge format={tournament.format} />
                    </span>
                  </div>
                  <div className="td-info-card">
                    <span className="td-info-label">MAX PLAYERS</span>
                    <span className="td-info-value td-info-number">
                      {tournament.max_participants}
                    </span>
                  </div>
                  <div className="td-info-card">
                    <span className="td-info-label">REGISTERED</span>
                    <span className="td-info-value td-info-number">
                      {tournament.participants_count}
                    </span>
                  </div>
                  <div className="td-info-card">
                    <span className="td-info-label">SPOTS LEFT</span>
                    <span className="td-info-value td-info-number">
                      {(tournament.max_participants || 0) - tournament.participants_count}
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <div className="td-footer-nav">
            <Link to="/tournaments" className="td-back-btn">
              ← BACK TO TOURNAMENTS
            </Link>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  )
}