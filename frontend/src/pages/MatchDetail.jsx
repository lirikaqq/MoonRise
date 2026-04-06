import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getMatchById } from '../api/matches'
import { useAuth } from '../context/AuthContext'
import Header from '../components/layout/Header'
import './MatchDetail.css'

const fmt = (num) => {
  if (num == null) return '0'
  if (Math.abs(num) >= 10000) return (num / 1000).toFixed(1) + 'k'
  return Math.round(num).toLocaleString('en-US')
}

export default function MatchDetail() {
  const { id: matchId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [match, setMatch] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overall')

  useEffect(() => {
    setLoading(true)
    getMatchById(matchId)
      .then(setMatch)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [matchId])

  const handleDelete = async () => {
    if (!window.confirm('Удалить этот матч? Действие необратимо.')) return
    try {
      const token = localStorage.getItem('moonrise_token')
      // ИСПРАВЛЕНО: Убран хардкод http://localhost:8000
      const res = await fetch(`/api/matches/${matchId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Ошибка удаления')
      navigate(-1)
    } catch (err) {
      alert(err.message)
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
    if (activeTab === 'overall') return match.players || []
    
    const rd = rounds.find(r => r.round_number === activeTab)
    if (!rd) return []
    
    return rd.players.map(rp => {
      const main = (match.players || []).find(mp => mp.player_name === rp.player_name)
      // ИСПРАВЛЕНО: Теперь team_id и user_id надежно подтягиваются из основной таблицы БД
      return { 
        ...rp, 
        id: rp.player_name, 
        user_id: main?.user_id || null, 
        team_id: main?.team_id || null 
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
          />
          <TeamTable
            team={match.team2}
            players={team2Players}
            isWinner={team2isWinner}
          />

          <Link to="/tournaments" className="md-back font-palui">‹ НАЗАД</Link>
        </div>
      </main>
    </div>
  )
}

function TeamTable({ team, players, isWinner }) {
  // ИСПРАВЛЕНО: Сортировка по "Импакту" (Урон + Хил), чтобы саппорты отображались честно
  const sorted = [...players].sort((a, b) => {
    const impactA = (a.hero_damage_dealt || 0) + (a.healing_dealt || 0);
    const impactB = (b.hero_damage_dealt || 0) + (b.healing_dealt || 0);
    return impactB - impactA;
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

              return (
                <tr key={p.id || p.player_name}>
                  <td className="md-col-player">
                    {p.user_id ? (
                      <Link to={`/players/${p.user_id}`} className="md-player-link font-ponter">
                        {p.player_name}
                      </Link>
                    ) : (
                      <span className="md-player-name font-ponter">{p.player_name}</span>
                    )}
                  </td>
                  <td className="md-col-kda font-digits">
                    <span className="md-k">{p.eliminations || 0}</span>
                    <span className="md-sep"> / </span>
                    <span className="md-d">{p.deaths || 0}</span>
                    <span className="md-sep"> / </span>
                    <span className="md-a">{assists}</span>
                  </td>
                  <td className="md-col-stat font-digits">{fmt(p.hero_damage_dealt)}</td>
                  <td className="md-col-stat font-digits">{fmt(p.healing_dealt)}</td>
                  <td className="md-col-stat font-digits">{fmt(p.damage_blocked)}</td>
                  <td className="md-col-stat md-col-acc font-digits">
                    {acc > 0 ? `${(acc * 100).toFixed(0)}%` : '—'}
                  </td>
                  <td className="md-col-heroes">
                    <div className="md-hero-list">
                      {heroes.map(h => (
                        <div
                          key={h.hero_name}
                          className="md-hero-badge font-palui"
                          title={`${h.hero_name} — ${Math.round(h.time_played || 0)}s`}
                        >
                          {h.hero_name.substring(0, 3).toUpperCase()}
                        </div>
                      ))}
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