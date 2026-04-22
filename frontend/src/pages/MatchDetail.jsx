import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom'
import { getMatchById, deleteMatch, getMatchKillFeed } from '../api/matches'
import { useAuth } from '../context/AuthContext'
import Header from '../components/layout/Header'
import './MatchDetail.css'

const fmt = (num) => {
  if (num == null) return '0'
  if (Math.abs(num) >= 10000) return (num / 1000).toFixed(1) + 'k'
  return Math.round(num).toLocaleString('en-US')
}

// Убирает Discord discriminator (#0000) из никнейма
const stripDiscriminator = (name) => {
  if (!name) return ''
  return name.replace(/#\d{4}$/, '')
}

export default function MatchDetail() {
  const { id: matchId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  const [match, setMatch] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overall')
  const [backUrl, setBackUrl] = useState('/tournaments')
  const [backLabel, setBackLabel] = useState('НАЗАД')
  const [heroModal, setHeroModal] = useState(null)
  const [killFeed, setKillFeed] = useState([])
  const [csTooltip, setCsTooltip] = useState(false)
  const [csTooltipY, setCsTooltipY] = useState(0)

  useEffect(() => {
    const prevState = location.state?.from
    if (prevState) {
      setBackUrl(prevState.url)
      setBackLabel(prevState.label || 'НАЗАД')
    }
  }, [location])

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getMatchById(matchId),
      getMatchKillFeed(matchId).catch(() => []),
    ])
      .then(([matchData, kfData]) => {
        setMatch(matchData)
        setKillFeed(kfData || [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [matchId])

  const handleDelete = async () => {
    if (!window.confirm('Удалить этот матч? Действие необратимо.')) return
    try {
      await deleteMatch(matchId)
      navigate(-1)
    } catch (err) {
      alert(err.message || 'Ошибка удаления')
    }
  }

  if (loading) return (
    <div className="md-page">
      <Header />
      <div className="md-loading">
        <div className="md-spinner" />
        <span>LOADING...</span>
      </div>
    </div>
  )

  if (error || !match) return (
    <div className="md-page">
      <Header />
      <div className="md-loading">
        <span>{error || 'NOT FOUND'}</span>
      </div>
    </div>
  )

  const rounds = match.round_stats || []
  const team1isWinner = match.winner_team_id === match.team1?.id
  const team2isWinner = match.winner_team_id === match.team2?.id

  const getPlayers = () => {
    // Подсчёт First Blood для каждого игрока (из kill feed)
    const fbCounts = {}
    killFeed.forEach(k => {
      if (k.is_first_blood) {
        fbCounts[k.killer_name] = (fbCounts[k.killer_name] || 0) + 1
      }
    })

    if (activeTab === 'overall') {
      return (match.players || []).map(p => ({
        ...p,
        first_blood_count: fbCounts[p.player_name] || 0,
      }))
    }

    const rd = rounds.find(r => r.round_number === activeTab)
    if (!rd) return []

    return rd.players.map(rp => {
      const main = (match.players || []).find(mp => mp.player_name === rp.player_name)
      return {
        ...rp,
        id: rp.player_name,
        user_id: main?.user_id || null,
        team_id: main?.team_id || null,
        heroes: main?.heroes || [],
        last_hero: main?.last_hero || null,
        is_mvp: main?.is_mvp || false,
        is_svp: main?.is_svp || false,
        contribution_score: main?.contribution_score || 0,
        first_blood_count: fbCounts[rp.player_name] || 0,
      }
    })
  }

  const allPlayers = getPlayers()
  const team1Players = allPlayers.filter(p => p.team_id === match.team1?.id)
  const team2Players = allPlayers.filter(p => p.team_id === match.team2?.id)

  const duration = match.duration_seconds || 0
  const mins = Math.floor(duration / 60)
  const secs = Math.round(duration % 60)

  return (
    <div className="md-page">
      <Header />
      <main className="md-main">
        <div className="md-container">

          <div className="md-header">
            <h1 className="md-map font-palui">{match.map_name}</h1>
            <div className="md-versus">
              <span className={`md-team-name font-ponter ${team1isWinner ? 'md-win' : 'md-lose'}`}>
                {match.team1?.name || 'Team 1'}
              </span>
              <span className="md-vs font-digits">VS</span>
              <span className={`md-team-name font-ponter ${team2isWinner ? 'md-win' : 'md-lose'}`}>
                {match.team2?.name || 'Team 2'}
              </span>
            </div>
            <p className="md-meta font-digits">
              {match.game_mode} · {mins}м {secs}с
            </p>
            {user?.role === 'admin' && (
              <button onClick={handleDelete} className="md-delete-btn font-palui">
                🗑 УДАЛИТЬ МАТЧ
              </button>
            )}
          </div>

          <div className="md-tabs">
            <button
              className={`md-tab font-digits ${activeTab === 'overall' ? 'md-tab--active' : ''}`}
              onClick={() => setActiveTab('overall')}
            >
              МАТЧ
            </button>
            {rounds.map((r, i) => (
              <button
                key={r.round_number}
                className={`md-tab font-digits ${activeTab === r.round_number ? 'md-tab--active' : ''}`}
                onClick={() => setActiveTab(r.round_number)}
              >
                РАУНД {i + 1}
              </button>
            ))}
          </div>

          <TeamTable
            team={match.team1}
            players={team1Players}
            isWinner={team1isWinner}
            onHeroClick={(player) => setHeroModal(player)}
            onCsHover={(show, y) => { setCsTooltip(show); setCsTooltipY(y); }}
          />
          <TeamTable
            team={match.team2}
            players={team2Players}
            isWinner={team2isWinner}
            onHeroClick={(player) => setHeroModal(player)}
            onCsHover={(show, y) => { setCsTooltip(show); setCsTooltipY(y); }}
          />

          {/* Глобальный тултип CS — один на всю страницу */}
          {csTooltip && (
            <div className="md-cs-tooltip md-cs-tooltip--global" style={{ top: `${csTooltipY + 16}px` }}>
              <div className="md-cs-tooltip-title">Contribution Score</div>
              <div className="md-cs-tooltip-desc">Комплексная метрика вклада игрока</div>
              <div className="md-cs-tooltip-formula">
                Elim × 500 + FB × 250 + Assists × 50<br />
                + Hero Damage + Healing<br />
                − Deaths × 750 + Blocked × 0.1
              </div>
              <div className="md-cs-tooltip-note">Чем выше — тем больше влияние на матч</div>
            </div>
          )}

          <Link to={backUrl} className="md-back font-palui">‹ {backLabel}</Link>
        </div>
      </main>

      {/* Модалка со всеми героями игрока */}
      {heroModal && (
        <div className="md-hero-modal-overlay" onClick={() => setHeroModal(null)}>
          <div className="md-hero-modal" onClick={(e) => e.stopPropagation()}>
            <div className="md-hero-modal-header">
              <span className="font-palui">{stripDiscriminator(heroModal.player_name)}</span>
              <button className="md-hero-modal-close" onClick={() => setHeroModal(null)}>✕</button>
            </div>
            <div className="md-hero-modal-list">
              {(heroModal.heroes || []).sort((a, b) => (b.time_played || 0) - (a.time_played || 0)).map(h => (
                <div key={h.hero_name} className="md-hero-modal-item">
                  <span className="md-hero-modal-item-name font-palui">{h.hero_name}</span>
                  <span className="md-hero-modal-item-time font-digits">{Math.round(h.time_played || 0)}s</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TeamTable({ team, players, isWinner, onHeroClick, onCsHover }) {
  const sorted = [...players].sort((a, b) => {
    const impactA = (a.hero_damage_dealt || 0) + (a.healing_dealt || 0)
    const impactB = (b.hero_damage_dealt || 0) + (b.healing_dealt || 0)
    return impactB - impactA
  })

  return (
    <div className="md-team-block">
      <div className={`md-team-header ${isWinner ? 'md-team-win' : 'md-team-lose'}`}>
        <span className="font-palui">{team?.name || '—'}</span>
        <span className="font-palui">{isWinner ? 'ПОБЕДА' : 'ПОРАЖЕНИЕ'}</span>
      </div>
      <div className="md-table-wrap">
        <table className="md-table">
          <thead>
            <tr>
              <th className="md-col-player font-digits">ИГРОК</th>
              <th className="md-col-kda font-digits">K / D / A</th>
              <th className="md-col-fb font-digits">FB</th>
              <th
                className="md-col-score font-digits md-col-score--tooltip"
                onMouseEnter={(e) => onCsHover(true, e.currentTarget.getBoundingClientRect().bottom)}
                onMouseLeave={() => onCsHover(false, 0)}
              >
                CS
              </th>
              <th className="md-col-stat font-digits">УРОН</th>
              <th className="md-col-stat font-digits">ЛЕЧЕНИЕ</th>
              <th className="md-col-stat font-digits">БЛОК</th>
              <th className="md-col-stat font-digits">ТОЧН.</th>
              <th className="md-col-heroes font-digits">ГЕРОИ</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(p => {
              const heroes = (p.heroes || []).sort((a, b) => (b.time_played || 0) - (a.time_played || 0))
              const topHero = heroes[0]
              const acc = topHero?.weapon_accuracy || p.weapon_accuracy || 0
              const assists = (p.defensive_assists || 0) + (p.offensive_assists || 0)
              const hasMoreHeroes = (p.heroes || []).length > 1
              const lastHeroName = p.last_hero || topHero?.hero_name

              return (
                <tr key={p.id || p.player_name}>
                  <td className="md-col-player">
                    <div className="md-player-cell">
                      {p.user_id ? (
                        <Link to={`/players/${p.user_id}`} className="md-player-link font-ponter">
                          {stripDiscriminator(p.player_name)}
                        </Link>
                      ) : (
                        <span className="md-player-name font-ponter">{stripDiscriminator(p.player_name)}</span>
                      )}
                      {/* MVP/SVP бейджи */}
                      <div className="md-badges">
                        {!!p.is_mvp && <span className="md-badge-mvp font-digits">MVP</span>}
                        {!!p.is_svp && <span className="md-badge-svp font-digits">SVP</span>}
                      </div>
                    </div>
                  </td>
                  <td className="md-col-kda font-digits">
                    <span className="md-k">{p.eliminations || 0}</span>
                    <span className="md-sep"> / </span>
                    <span className="md-d">{p.deaths || 0}</span>
                    <span className="md-sep"> / </span>
                    <span className="md-a">{assists}</span>
                  </td>
                  <td className="md-col-fb">
                    {p.first_blood_count > 0 ? (
                      <span className="md-fb-badge font-digits">{p.first_blood_count}</span>
                    ) : (
                      <span className="md-fb-none font-digits">0</span>
                    )}
                  </td>
                  <td className="md-col-score font-digits">
                    {fmt(p.contribution_score || 0)}
                  </td>
                  <td className="md-col-stat font-digits">{fmt(p.hero_damage_dealt)}</td>
                  <td className="md-col-stat font-digits">{fmt(p.healing_dealt)}</td>
                  <td className="md-col-stat font-digits">{fmt(p.damage_blocked)}</td>
                  <td className="md-col-stat md-col-acc font-digits">
                    {acc > 0 ? `${(acc * 100).toFixed(0)}%` : '—'}
                  </td>
                  <td className="md-col-heroes">
                    <div className="md-hero-list">
                      {/* Последний герой — кликабельный */}
                      {lastHeroName && (
                        <div
                          className={`md-hero-badge md-hero-last font-palui ${hasMoreHeroes ? 'md-hero-clickable' : ''}`}
                          title={hasMoreHeroes ? `${stripDiscriminator(p.player_name)} — все герои` : lastHeroName}
                          onClick={hasMoreHeroes ? () => onHeroClick(p) : undefined}
                        >
                          {lastHeroName.substring(0, 3).toUpperCase()}
                          {hasMoreHeroes && <span className="md-hero-arrow">›</span>}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}