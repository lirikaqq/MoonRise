import { useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import MatchesHistoryHeader from './MatchesHistoryHeader'
import MatchesHistoryTable from './MatchesHistoryTable'
import styles from './MatchesHistory.module.css'

const DEMO_MATCHES = [
  {
    id: 1,
    team1_name: 'Carnivorous',
    team2_name: 'Carnivorous',
    team1_score: 0,
    team2_score: 3,
    stage: 'playoffs',
    round_number: 1,
    logs_url: '+',
  },
  {
    id: 2,
    team1_name: 'Carnivorous',
    team2_name: 'Carnivorous',
    team1_score: 0,
    team2_score: 3,
    stage: 'group_stage',
    round_number: 2,
    logs_url: '-',
  },
]

const stageKeyToApi = (stageFilter) => {
  const s = String(stageFilter).toUpperCase()
  if (s === 'GROUP STAGE') return 'group_stage'
  if (s === 'PLAYOFFS') return 'playoffs'
  if (s === 'FINALS') return 'finals'
  return 'ALL'
}

export default function MatchesHistory({ tournamentId }) {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [searchQuery, setSearchQuery] = useState('')
  const [stageFilter, setStageFilter] = useState('ALL')
  const [roundFilter, setRoundFilter] = useState('ALL')

  const [expandedLogs, setExpandedLogs] = useState({})

  useEffect(() => {
    // Пока без реального API: демонстрационные данные.
    // В будущем здесь будет fetch: GET /api/tournaments/{tournamentId}/matches
    setLoading(true)
    setError('')
    Promise.resolve()
      .then(() => {
        setMatches(DEMO_MATCHES)
      })
      .catch((e) => {
        console.error(e)
        setError('Failed to load matches')
        setMatches([])
      })
      .finally(() => setLoading(false))
  }, [tournamentId])

  const filteredMatches = useMemo(() => {
    const q = (searchQuery || '').trim().toLowerCase()
    const stage = stageKeyToApi(stageFilter)
    const round = roundFilter === 'ALL' ? null : Number(roundFilter)

    return matches.filter((m) => {
      const name = `${m.team1_name || ''} ${m.team2_name || ''}`.toLowerCase()
      const matchSearch = !q || name.includes(q)
      const matchStage = stage === 'ALL' || String(m.stage || '').toLowerCase() === stage
      const matchRound = round === null || Number(m.round_number) === round
      return matchSearch && matchStage && matchRound
    })
  }, [matches, searchQuery, stageFilter, roundFilter])

  const onToggleLogs = (matchId) => {
    setExpandedLogs((prev) => ({
      ...prev,
      [matchId]: !prev[matchId],
    }))
  }

  return (
    <div className={styles.container}>
      <MatchesHistoryHeader
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        stageFilter={stageFilter}
        onStageFilterChange={setStageFilter}
        roundFilter={roundFilter}
        onRoundFilterChange={setRoundFilter}
      />

      {loading ? (
        <div className={styles.meta} style={{ padding: '10px 0' }}>
          LOADING MATCHES...
        </div>
      ) : error ? (
        <div className={styles.meta} style={{ padding: '10px 0', color: '#ff7b7b' }}>
          {error}
        </div>
      ) : filteredMatches.length === 0 ? (
        <div className={styles.meta} style={{ padding: '10px 0' }}>
          NO MATCHES
        </div>
      ) : (
        <MatchesHistoryTable
          matches={filteredMatches}
          expandedLogs={expandedLogs}
          onToggleLogs={onToggleLogs}
        />
      )}
    </div>
  )
}

MatchesHistory.propTypes = {
  tournamentId: PropTypes.number.isRequired,
}
