import { useState, useEffect, useCallback } from 'react'
import client from '../../api/client'
import { reportEncounterResult } from '../../api/matches'
import { useAuth } from '../../context/AuthContext'

// ==================== HELPER: Build bracket tree from encounters ====================
function buildBracketTree(encounters, teams) {
  const rounds = {}
  encounters.forEach(enc => {
    const rnd = enc.round_number || 1
    if (!rounds[rnd]) rounds[rnd] = []
    rounds[rnd].push({
      ...enc,
      team1: teams.find(t => t.id === enc.team1_id) || null,
      team2: teams.find(t => t.id === enc.team2_id) || null,
      winner: teams.find(t => t.id === enc.winner_team_id) || null,
    })
  })
  return Object.entries(rounds)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([round, matches]) => ({ round: Number(round), matches }))
}

// ==================== DRAG & DROP SLOTS ====================
function SeedingSlot({ roundIdx, matchIdx, slotIdx, value, onDrop, onDragStart, teams }) {
  const team = value ? teams.find(t => t.id === value) : null
  const isEmpty = !value

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  return (
    <div
      className={`bracket-slot ${isEmpty ? 'bracket-slot--empty' : 'bracket-slot--filled'}`}
      onDragOver={handleDragOver}
      onDrop={(e) => {
        e.preventDefault()
        const teamId = parseInt(e.dataTransfer.getData('text/plain'))
        if (teamId) onDrop(roundIdx, matchIdx, slotIdx, teamId)
      }}
    >
      {team ? (
        <div
          className="bracket-slot-team"
          draggable
          onDragStart={(e) => onDragStart(e, team.id)}
          title={team.name}
        >
          <span className="bracket-slot-team-name">{team.name}</span>
        </div>
      ) : (
        <span className="bracket-slot-placeholder">Команда {slotIdx + 1}</span>
      )}
    </div>
  )
}

// ==================== MATCH BLOCK (Published) ====================
function MatchBlock({ match, onClick, teams, onResultSaved }) {
  const { user } = useAuth()
  const [showResultModal, setShowResultModal] = useState(false)
  const [score1, setScore1] = useState('')
  const [score2, setScore2] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const team1 = teams.find(t => t.id === match.team1_id)
  const team2 = teams.find(t => t.id === match.team2_id)
  const isCompleted = !!match.winner_team_id
  const isAdmin = user?.role === 'admin'

  // Both teams present but no result → show "Report result" button for admin
  const canReportResult = isAdmin && !isCompleted && match.team1_id && match.team2_id

  const handleSave = async () => {
    const s1 = parseInt(score1, 10)
    const s2 = parseInt(score2, 10)
    if (isNaN(s1) || isNaN(s2)) {
      setError('Введите корректный счёт')
      return
    }
    if (s1 === s2) {
      setError('Ничья недопустима в single-elimination')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await reportEncounterResult(match.id, s1, s2)
      setShowResultModal(false)
      setScore1('')
      setScore2('')
      onResultSaved?.(match.id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при сохранении')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div
        className={`bracket-match ${isCompleted ? 'bracket-match--completed' : 'bracket-match--pending'}`}
        onClick={() => onClick(match)}
      >
        <div className={`bracket-match-team ${match.winner_team_id === match.team1_id ? 'winner' : ''}`}>
          <span className="bracket-match-team-name" title={team1?.name || 'TBD'}>{team1?.name || 'TBD'}</span>
          <span className="bracket-match-score">{match.team1_score ?? '-'}</span>
        </div>
        <div className="bracket-match-divider">—</div>
        <div className={`bracket-match-team ${match.winner_team_id === match.team2_id ? 'winner' : ''}`}>
          <span className="bracket-match-team-name" title={team2?.name || 'TBD'}>{team2?.name || 'TBD'}</span>
          <span className="bracket-match-score">{match.team2_score ?? '-'}</span>
        </div>
        <div className="bracket-match-status">
          {isCompleted ? '✓' : '⏳'}
        </div>

        {/* Кнопка "Сообщить результат" — только админ */}
        {canReportResult && (
          <button
            className="bracket-match-report-btn"
            onClick={(e) => {
              e.stopPropagation()
              setShowResultModal(true)
            }}
            title="Сообщить результат"
          >
            ✏️
          </button>
        )}
      </div>

      {/* Модальное окно результата */}
      {showResultModal && (
        <div className="modal-overlay" onClick={() => setShowResultModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
            background: '#1a2a30',
            border: '1px solid #13AD91',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '400px',
            width: '90%',
            color: '#fff',
          }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '18px', color: '#A7F2A2' }}>
              Сообщить результат
            </h3>
            <p style={{ margin: '0 0 12px', fontSize: '13px', color: '#A7F2A2' }}>
              {team1?.name || 'Команда 1'} vs {team2?.name || 'Команда 2'}
            </p>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '12px', color: '#A7F2A2', display: 'block', marginBottom: '4px' }}>
                  {team1?.name || 'Команда 1'}
                </label>
                <input
                  type="number"
                  min="0"
                  value={score1}
                  onChange={(e) => setScore1(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    background: '#111B25',
                    border: '1px solid #13AD91',
                    borderRadius: '4px',
                    color: '#fff',
                    fontSize: '16px',
                    textAlign: 'center',
                    boxSizing: 'border-box',
                  }}
                  placeholder="0"
                />
              </div>
              <span style={{ fontSize: '20px', color: '#A7F2A2' }}>:</span>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '12px', color: '#A7F2A2', display: 'block', marginBottom: '4px' }}>
                  {team2?.name || 'Команда 2'}
                </label>
                <input
                  type="number"
                  min="0"
                  value={score2}
                  onChange={(e) => setScore2(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    background: '#111B25',
                    border: '1px solid #13AD91',
                    borderRadius: '4px',
                    color: '#fff',
                    fontSize: '16px',
                    textAlign: 'center',
                    boxSizing: 'border-box',
                  }}
                  placeholder="0"
                />
              </div>
            </div>
            {error && (
              <p style={{ margin: '0 0 12px', fontSize: '13px', color: '#ff6b6b' }}>
                {error}
              </p>
            )}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                className="admin-btn"
                onClick={() => { setShowResultModal(false); setError(null); setScore1(''); setScore2('') }}
                disabled={saving}
              >
                Отмена
              </button>
              <button
                className="admin-btn admin-btn--primary"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// ==================== SWISS / RR LIST VIEW ====================
function SwissListView({ encounters, teams, onMatchClick }) {
  const grouped = encounters.reduce((acc, enc) => {
    const rnd = enc.round_number || 1
    if (!acc[rnd]) acc[rnd] = []
    acc[rnd].push(enc)
    return acc
  }, {})

  return (
    <div className="swiss-list">
      {Object.entries(grouped)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([round, matches]) => (
          <div key={round} className="swiss-round">
            <h4 className="swiss-round-title">Раунд {round}</h4>
            <div className="swiss-matches">
              {matches.map(enc => {
                const t1 = teams.find(t => t.id === enc.team1_id)
                const t2 = teams.find(t => t.id === enc.team2_id)
                return (
                  <div
                    key={enc.id}
                    className={`swiss-match-card ${enc.winner_team_id ? 'swiss-match--completed' : 'swiss-match--pending'}`}
                    onClick={() => onMatchClick(enc)}
                  >
                    <div className="swiss-match-teams">
                      <span className={`swiss-match-team-name ${enc.winner_team_id === enc.team1_id ? 'winner' : ''}`} title={t1?.name || '—'}>{t1?.name || '—'}</span>
                      <span className="swiss-match-score">{enc.team1_score ?? 0} : {enc.team2_score ?? 0}</span>
                      <span className={`swiss-match-team-name ${enc.winner_team_id === enc.team2_id ? 'winner' : ''}`} title={t2?.name || '—'}>{t2?.name || '—'}</span>
                    </div>
                    <span className="swiss-match-status">
                      {enc.winner_team_id ? 'Завершён' : 'Не сыгран'}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
    </div>
  )
}

// ==================== MAIN COMPONENT ====================
export default function InteractiveBracket({ tournamentId, structureType, teams, encounters, onMatchClick, onSeedingComplete, onEncounterUpdated }) {
  const isSwissOrRR = ['SWISS', 'ROUND_ROBIN', 'GROUPS_PLUS_PLAYOFF'].includes(structureType)
  
  // Seeding state
  const [seedingMode, setSeedingMode] = useState(null) // 'random' | 'manual'
  const [seedingSlots, setSeedingSlots] = useState([]) // [{round, matches: [[team1Id, team2Id], ...]}]
  const [draggingTeamId, setDraggingTeamId] = useState(null)

  // Initialize seeding slots when teams change
  useEffect(() => {
    if (!seedingMode || teams.length < 2) return
    const matchCount = Math.ceil(teams.length / 2)
    const slots = Array.from({ length: matchCount }, () => [null, null])
    setSeedingSlots([{ round: 1, matches: slots }])
  }, [seedingMode, teams.length])

  // Drag handlers
  const handleDragStart = (e, teamId) => {
    setDraggingTeamId(teamId)
    e.dataTransfer.setData('text/plain', teamId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDropSlot = (roundIdx, matchIdx, slotIdx, teamId) => {
    if (!teamId) return
    // Check if team is already in another slot
    const alreadyPlaced = seedingSlots[roundIdx].matches.some((pair, mi) =>
      mi !== matchIdx && (pair[0] === teamId || pair[1] === teamId)
    )
    if (alreadyPlaced) return

    setSeedingSlots(prev => {
      const next = [...prev]
      next[roundIdx] = {
        ...next[roundIdx],
        matches: next[roundIdx].matches.map((pair, mi) =>
          mi === matchIdx ? pair.map((id, si) => si === slotIdx ? teamId : id) : pair
        )
      }
      return next
    })
  }

  // Auto-seeding (random)
  const handleAutoSeed = async () => {
    const shuffled = [...teams].sort(() => Math.random() - 0.5)
    const pairs = []
    for (let i = 0; i < shuffled.length - 1; i += 2) {
      pairs.push([shuffled[i].id, shuffled[i + 1].id])
    }
    // Create encounters
    for (const [t1, t2] of pairs) {
      await client.post('/matches/encounters', {
        tournament_id: tournamentId,
        team1_id: t1,
        team2_id: t2,
        stage: 'Round 1',
        round_number: 1,
      })
    }
    await onSeedingComplete()
    setSeedingMode(null)
  }

  // Publish manual seeding
  const handlePublishSeeding = async () => {
    const pairs = seedingSlots[0].matches.filter(([a, b]) => a && b)
    for (const [t1, t2] of pairs) {
      await client.post('/matches/encounters', {
        tournament_id: tournamentId,
        team1_id: t1,
        team2_id: t2,
        stage: 'Round 1',
        round_number: 1,
      })
    }
    await onSeedingComplete()
    setSeedingMode(null)
  }

  const bracketTree = buildBracketTree(encounters, teams)
  const hasEncounters = encounters.length > 0

  // ==================== RENDER ====================
  return (
    <div className="interactive-bracket">
      {/* Seeding Panel */}
      {!hasEncounters && !seedingMode && (
        <div className="bracket-seeding-panel">
          <h3>Генерация сетки</h3>
          <p className="bracket-hint">Выберите стратегию посева для создания первого раунда</p>
          <div className="bracket-seeding-btns">
            <button className="admin-btn admin-btn--primary" onClick={handleAutoSeed} disabled={teams.length < 2}>
              🎲 Случайный посев
            </button>
            <button className="admin-btn admin-btn--primary" onClick={() => setSeedingMode('manual')} disabled={teams.length < 2}>
              ✋ Ручной посев
            </button>
            <button className="admin-btn" disabled title="В разработке">📊 По рейтингу (скоро)</button>
          </div>
        </div>
      )}

      {/* Manual Seeding UI */}
      {seedingMode === 'manual' && !hasEncounters && (
        <div className="manual-seeding-ui">
          <div className="manual-seeding-header">
            <h3>Ручной посев</h3>
            <div className="manual-seeding-actions">
              <button
                className="admin-btn admin-btn--primary"
                onClick={handlePublishSeeding}
                disabled={seedingSlots[0]?.matches.some(([a, b]) => !a || !b)}
              >
                Подтвердить и опубликовать ({seedingSlots[0]?.matches.filter(([a, b]) => a && b).length} пар)
              </button>
              <button className="admin-btn" onClick={() => setSeedingMode(null)}>Отмена</button>
            </div>
          </div>
          <p className="bracket-hint">Перетащите команду из списка в пустой слот. Кликните на команду в слоте, чтобы убрать её.</p>
          
          <div className="manual-seeding-layout">
            <div className="manual-seeding-pool">
              <h4>Нераспределённые</h4>
              <div className="manual-seeding-team-list">
                {teams.map(t => (
                  <div
                    key={t.id}
                    className="manual-seeding-team-item"
                    draggable
                    onDragStart={(e) => handleDragStart(e, t.id)}
                    title={t.name}
                  >
                    {t.name}
                  </div>
                ))}
              </div>
            </div>
            <div className="manual-seeding-bracket">
              <h4>Сетка первого раунда</h4>
              <div className="bracket-round">
                {seedingSlots[0]?.matches.map((pair, mi) => (
                  <div key={mi} className="bracket-match-seeding">
                    <SeedingSlot
                      roundIdx={0} matchIdx={mi} slotIdx={0} value={pair[0]}
                      onDrop={handleDropSlot} onDragStart={handleDragStart} teams={teams}
                    />
                    <span className="bracket-vs">vs</span>
                    <SeedingSlot
                      roundIdx={0} matchIdx={mi} slotIdx={1} value={pair[1]}
                      onDrop={handleDropSlot} onDragStart={handleDragStart} teams={teams}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Published Bracket / Swiss List */}
      {hasEncounters && isSwissOrRR ? (
        <SwissListView encounters={encounters} teams={teams} onMatchClick={onMatchClick} />
      ) : hasEncounters ? (
        <div className="bracket-tree">
          {bracketTree.map(({ round, matches }) => (
            <div key={round} className="bracket-round">
              <div className="bracket-round-label">Раунд {round}</div>
              <div className="bracket-round-matches">
                {matches.map(m => (
                  <MatchBlock key={m.id} match={m} teams={teams} onClick={onMatchClick} onResultSaved={onEncounterUpdated} />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
