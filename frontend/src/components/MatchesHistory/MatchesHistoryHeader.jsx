import PropTypes from 'prop-types'
import styles from './MatchesHistory.module.css'

export default function MatchesHistoryHeader({
  searchQuery,
  onSearchQueryChange,
  stageFilter,
  onStageFilterChange,
  roundFilter,
  onRoundFilterChange,
}) {
  return (
    <div className={styles.header}>
      <div className={styles.searchWrap}>
        <img src="/assets/icons/lupa.svg" alt="" className={styles.searchIcon} />
        <input
          className={styles.searchInput}
          placeholder="SEARCH TEAM..."
          value={searchQuery}
          onChange={(e) => onSearchQueryChange(e.target.value)}
        />
      </div>

      <select
        className={styles.select}
        value={stageFilter}
        onChange={(e) => onStageFilterChange(e.target.value)}
      >
        <option value="ALL">ALL</option>
        <option value="GROUP STAGE">GROUP STAGE</option>
        <option value="PLAYOFFS">PLAYOFFS</option>
        <option value="FINALS">FINALS</option>
      </select>

      <select
        className={styles.select}
        value={roundFilter}
        onChange={(e) => onRoundFilterChange(e.target.value)}
      >
        <option value="ALL">ALL</option>
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
        <option value="4">4</option>
      </select>
    </div>
  )
}

MatchesHistoryHeader.propTypes = {
  searchQuery: PropTypes.string.isRequired,
  onSearchQueryChange: PropTypes.func.isRequired,
  stageFilter: PropTypes.string.isRequired,
  onStageFilterChange: PropTypes.func.isRequired,
  roundFilter: PropTypes.string.isRequired,
  onRoundFilterChange: PropTypes.func.isRequired,
}
