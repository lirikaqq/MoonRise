import React from 'react';
import './StatsBottomRow.css';

export default function StatsBottomRow({ stats }) {
  const cards = [
    { label: 'WINRATE', value: stats?.winrate || '100%', sub: stats?.winrateSub || '5 FROM 12' },
    { label: 'KDA RATIO', value: stats?.kdaRatio || '4.57', sub: stats?.kdaSub || '33 FROM 100' },
    { label: 'ELIMS', value: stats?.elims || '24.28', sub: stats?.elimsSub || '20 FROM 100' },
    { label: 'DEATHS', value: stats?.deaths || '6.89', sub: stats?.deathsSub || '26 FROM 100' },
  ];

  return (
    <div className="stats-bottom-row">
      {cards.map((card) => (
        <div key={card.label} className="stat-card-large">
          <div className="stat-card-large__accent-line" />
          <div className="stat-card-large__content">
            <div className="stat-card-large__label">{card.label}</div>
            <div className="stat-card-large__value">{card.value}</div>
            <div className="stat-card-large__sub">{card.sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
