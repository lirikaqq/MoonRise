import { useState, useEffect } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { getEncounterById } from '../api/matches'
import Header from '../components/layout/Header'
import './EncounterDetail.css'

export default function EncounterDetail() {
  const { id: encounterId } = useParams()
  const location = useLocation()

  const [encounter, setEncounter] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedMatchId, setSelectedMatchId] = useState(null)
  const [backUrl, setBackUrl] = useState('/tournaments')
  const [backLabel, setBackLabel] = useState('НАЗАД')

  useEffect(() => {
    const prevState = location.state?.from
    if (prevState) {
      setBackUrl(prevState.url)
      setBackLabel(prevState.label || 'НАЗАД')
    }
  }, [location])

  useEffect(() => {
    setLoading(true)
    getEncounterById(encounterId)
      .then((data) => {
        setEncounter(data)
        // Выбираем первый матч по умолчанию
        if (data?.matches?.length > 0) {
          setSelectedMatchId(data.matches[0].id)
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [encounterId])

  if (loading) return (
    <div className="ed-page">
      <Header />
      <div className="ed-loading">
        <div className="ed-spinner" />
        <span>LOADING...</span>
      </div>
    </div>
  )

  if (error || !encounter) return (
    <div className="ed-page">
      <Header />
      <div className="ed-loading">
        <span>{error || 'NOT FOUND'}</span>
      </div>
    </div>
  )

  const team1Win = encounter.team1_score > encounter.team2_score
  const team2Win = encounter.team2_score > encounter.team1_score
  const matches = encounter.matches || []
  const selectedMatch = matches.find(m => m.id === selectedMatchId)

  return (
    <div className="ed-page">
      <Header />
      <main className="ed-main">
        <div className="ed-container">

          {/* Заголовок Encounter */}
          <div className="ed-header">
            <div className="ed-score-line">
              <span className={`ed-team-name font-palui ${team1Win ? 'ed-win' : ''}`}>
                {encounter.team1?.name || 'Team 1'}
              </span>
              <div className="ed-score">
                <span className={`ed-score-num font-digits ${team1Win ? 'ed-score-win' : ''}`}>
                  {encounter.team1_score}
                </span>
                <span className="ed-score-sep font-digits">:</span>
                <span className={`ed-score-num font-digits ${team2Win ? 'ed-score-win' : ''}`}>
                  {encounter.team2_score}
                </span>
              </div>
              <span className={`ed-team-name font-palii ${team2Win ? 'ed-win' : ''}`}>
                {encounter.team2?.name || 'Team 2'}
              </span>
            </div>
            {encounter.stage && (
              <span className="ed-stage font-digits">{encounter.stage.toUpperCase()}</span>
            )}
          </div>

          {/* Карты — кликабельные */}
          <div className="ed-maps">
            {matches.map((m, i) => {
              const isMatchWin = m.winner_team_id === encounter.team1_id || m.winner_team_id === encounter.team2_id
              const mapNum = i + 1
              return (
                <Link
                  key={m.id}
                  to={`/matches/${m.id}`}
                  state={{ from: { url: `/encounters/${encounterId}`, label: 'ENCOUNTER' } }}
                  className={`ed-map-card ${selectedMatchId === m.id ? 'ed-map-card--active' : ''}`}
                  onClick={() => setSelectedMatchId(m.id)}
                >
                  <span className="ed-map-num font-digits">{mapNum}</span>
                  <span className="ed-map-name font-palii">{m.map_name}</span>
                  <span className="ed-map-mode font-digits">{m.game_mode || ''}</span>
                </Link>
              )
            })}
          </div>

          {/* Выбранный матч — краткая информация */}
          {selectedMatch && (
            <div className="ed-match-info">
              <Link to={`/matches/${selectedMatch.id}`} className="ed-match-link"
                state={{ from: { url: `/encounters/${encounterId}`, label: 'ENCOUNTER' } }}>
                <span className="font-palii">ПОДРОБНЕЕ →</span>
              </Link>
            </div>
          )}

          <Link to={backUrl} className="ed-back font-palii">‹ {backLabel}</Link>
        </div>
      </main>
    </div>
  )
}
