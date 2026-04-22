import PropTypes from 'prop-types'
import MatchRow from './MatchRow'
import styles from './MatchesHistory.module.css'

const STAGE_TITLES = {
  group_stage: 'GROUP STAGE',
  playoffs: 'PLAYOFFS',
  finals: 'FINALS',
}

export default function MatchesHistoryTable({ matches, expandedLogs, onToggleLogs }) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>NAME</th>
            <th className={styles.th}>ROUND</th>
            <th className={styles.th}>STAGE</th>
            <th className={styles.th}>SCORE</th>
            <th className={styles.th}>LOGS</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((m) => (
            <MatchRow
              key={m.id}
              match={m}
              expanded={Boolean(expandedLogs[m.id])}
              onToggleLogs={onToggleLogs}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

MatchesHistoryTable.propTypes = {
  matches: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
  })).isRequired,
  expandedLogs: PropTypes.objectOf(PropTypes.bool).isRequired,
  onToggleLogs: PropTypes.func.isRequired,
}
