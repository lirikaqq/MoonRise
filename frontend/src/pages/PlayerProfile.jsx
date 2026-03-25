import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import './PlayerProfile.css'

export default function PlayerProfile() {
  const { id } = useParams()
  const { user: currentUser } = useAuth()
  const [player, setPlayer] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const token = localStorage.getItem('moonrise_token')
        const res = await fetch(`/api/players/${id}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        if (!res.ok) throw new Error('Player not found')
        const data = await res.json()
        setPlayer(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const isOwnProfile = currentUser && currentUser.id === parseInt(id)

  if (loading) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-main">
          <div className="profile-loading">
            <div className="profile-loading-spinner"></div>
            <span>LOADING...</span>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  if (error || !player) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-main">
          <div className="profile-not-found">
            <p>PLAYER NOT FOUND</p>
            <Link to="/tournaments" className="profile-back-btn">← BACK</Link>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  const primaryTag = player.battletags?.find(t => t.is_primary) || player.battletags?.[0]

  return (
    <div className="profile-page">
      <Header />

      <main className="profile-main">
        <div className="profile-container">

          {/* Хлебные крошки */}
          <div className="profile-breadcrumb">
            <Link to="/tournaments">TOURNAMENTS</Link>
            <span className="profile-breadcrumb-sep">›</span>
            <span>PLAYERS</span>
            <span className="profile-breadcrumb-sep">›</span>
            <span>{player.username.toUpperCase()}</span>
          </div>

          <div className="profile-layout">

            {/* ЛЕВАЯ КОЛОНКА */}
            <div className="profile-sidebar">

              {/* Аватар + имя */}
              <div className="profile-card">
                <div className="profile-avatar-wrap">
                  {player.avatar_url ? (
                    <img
                      src={player.avatar_url}
                      alt={player.username}
                      className="profile-avatar"
                    />
                  ) : (
                    <div className="profile-avatar-placeholder">
                      {player.username[0].toUpperCase()}
                    </div>
                  )}
                  <div className="profile-avatar-border"></div>
                </div>

                <h1 className="profile-username">
                  {player.username.toUpperCase()}
                </h1>

                {/* Роль */}
                <div className="profile-role">
                  <span className={`profile-role-badge role-${player.role}`}>
                    {player.role.toUpperCase()}
                  </span>
                </div>

                {/* BattleTag */}
                {primaryTag && (
                  <div className="profile-battletag">
                    <span className="profile-battletag-icon">⚡</span>
                    <span className="profile-battletag-text">{primaryTag.tag}</span>
                  </div>
                )}

                {/* Дивизион */}
                {player.division && (
                  <div className="profile-division">
                    <span className="profile-division-label">DIVISION</span>
                    <span className="profile-division-value">{player.division.toUpperCase()}</span>
                  </div>
                )}

                {/* Статус */}
                <div className="profile-status">
                  <span className="profile-status-dot"></span>
                  <span className="profile-status-text">ONLINE</span>
                </div>
              </div>

              {/* Статистика */}
              <div className="profile-stats-card">
                <div className="profile-section-title">
                  <span className="profile-section-dot">•</span>
                  STATISTICS
                </div>
                <div className="profile-stats-grid">
                  <div className="profile-stat">
                    <span className="profile-stat-value">—</span>
                    <span className="profile-stat-label">WIN RATE</span>
                  </div>
                  <div className="profile-stat">
                    <span className="profile-stat-value">—</span>
                    <span className="profile-stat-label">K/D RATIO</span>
                  </div>
                  <div className="profile-stat">
                    <span className="profile-stat-value">{player.reputation_score}</span>
                    <span className="profile-stat-label">REPUTATION</span>
                  </div>
                  <div className="profile-stat">
                    <span className="profile-stat-value">—</span>
                    <span className="profile-stat-label">TOURNAMENTS</span>
                  </div>
                </div>
              </div>

              {/* BattleTags */}
              {player.battletags?.length > 0 && (
                <div className="profile-tags-card">
                  <div className="profile-section-title">
                    <span className="profile-section-dot">•</span>
                    BATTLE TAGS
                  </div>
                  <div className="profile-tags-list">
                    {player.battletags.map(tag => (
                      <div key={tag.id} className="profile-tag-row">
                        <span className="profile-tag-text">{tag.tag}</span>
                        {tag.is_primary && (
                          <span className="profile-tag-primary">PRIMARY</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Кнопка редактирования (только для своего профиля) */}
              {isOwnProfile && (
                <button className="profile-edit-btn">
                  EDIT PROFILE
                </button>
              )}

            </div>

            {/* ПРАВАЯ КОЛОНКА */}
            <div className="profile-content">

              {/* Табы */}
              <div className="profile-tabs">
                <button className="profile-tab active">TOURNAMENT HISTORY</button>
                <button className="profile-tab">ACHIEVEMENTS</button>
              </div>

              <div className="profile-tab-content">

                {/* Tournament history — заглушка */}
                <div className="profile-empty-state">
                  <div className="profile-empty-icon">🏆</div>
                  <p className="profile-empty-title">NO TOURNAMENTS YET</p>
                  <p className="profile-empty-sub">
                    TOURNAMENT HISTORY WILL APPEAR HERE
                  </p>
                  <Link to="/tournaments" className="profile-find-btn">
                    FIND TOURNAMENT
                  </Link>
                </div>

              </div>

            </div>

          </div>

        </div>
      </main>

      <Footer />
    </div>
  )
}