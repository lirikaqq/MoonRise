import React from 'react';
import './Bracket.css';

const MatchCard = ({ match }) => {
  if (!match || match.isEmpty) {
    return (
      <div className="match-card empty">
        <div className="match-card-inner">
          <div className="match-row">
            <span className="team-name">—</span>
            <span className="team-score">0</span>
          </div>
          <div className="match-row">
            <span className="team-name">—</span>
            <span className="team-score">0</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="match-card">
      <div className="match-card-inner">
        <div className="match-row">
          <span className={`team-name ${match.team1.isWinner ? 'winner' : ''}`}>
            {match.team1.name}
          </span>
          <span className={`team-score ${match.team1.isWinner ? 'winner' : ''}`}>
            {match.team1.score}
          </span>
        </div>
        <div className="match-row">
          <span className={`team-name ${match.team2.isWinner ? 'winner' : ''}`}>
            {match.team2.name}
          </span>
          <span className={`team-score ${match.team2.isWinner ? 'winner' : ''}`}>
            {match.team2.score}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MatchCard;