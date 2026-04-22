import PropTypes from 'prop-types'
import styles from './MatchesHistory.module.css'

export default function MatchRow({ match, expanded, onToggleLogs, onRowClick }) {
  const stageLabel = (() => {
    const s = (match.stage || '').toLowerCase()
    if (s === 'group_stage') return 'GROUP STAGE'
    if (s === 'playoffs') return 'PLAYOFFS'
    if (s === 'finals') return 'FINALS'
    return (match.stage || '—').toUpperCase()
  })()

  return (
    <tr className={styles.tr}>
      <td className={styles.td}>
        <div className={styles.teamName}>
          {match.team1_name} vs {match.team2_name}
        </div>
        <div className={styles.meta}>
          SCORE: {match.team1_score} - {match.team2_score}
        </div>
      </td>

      <td className={styles.td}>#{match.round_number}</td>
      <td className={styles.td}>{stageLabel}</td>
      <td className={styles.td}>
        {match.team1_score} : {match.team2_score}
      </td>

      <td className={styles.td}>
        <button
          type="button"
          className={styles.logsBtn}
          onClick={(e) => {
            e.stopPropagation()
            onToggleLogs(match.id)
          }}
          aria-label={expanded ? 'Hide logs' : 'Show logs'}
        >
          <span className={styles.logsState}>
            {expanded ? '-' : '+'}
          </span>
          <span>LOGS</span>
        </button>

        {expanded && match.logs_url && (
          <div className={styles.meta} style={{ marginTop: 8 }}>
            <a href={match.logs_url} target="_blank" rel="noreferrer" style={{ color: '#7CFFCB' }}>
              Open
            </a>
          </div>
        )}

        {expanded && (!match.logs_url || match.logs_url === '-') && (
          <div className={styles.meta} style={{ marginTop: 8 }}>
            Нет лога
          </div>
        )}
      </td>

    </tr>
  )
}

MatchRow.propTypes = {
  match: PropTypes.shape({
    id: PropTypes.number.isRequired,
    team1_name: PropTypes.string,
    team2_name: PropTypes.string,
    team1_score: PropTypes.number,
    team2_score: PropTypes.number,
    stage: PropTypes.string,
    round_number: PropTypes.number,
    logs_url: PropTypes.string,
  }).isRequired,
  expanded: PropTypes.bool,
  onToggleLogs: PropTypes.func.isRequired,
  onRowClick: PropTypes.func,
}
