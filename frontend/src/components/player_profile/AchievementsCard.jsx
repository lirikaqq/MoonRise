import React from 'react';
import './AchievementsCard.css';

const ACHIEVEMENTS = [
  { id: 1, src: '/assets/icons/icon-role-tank.svg', unlocked: true },
  { id: 2, src: '/assets/icons/icon-role-flex.svg', unlocked: true },
  { id: 3, src: '/assets/icons/icon-role-dps.svg', unlocked: true },
  { id: 4, src: '/assets/icons/icon-role-sup.svg', unlocked: true },
  { id: 5, src: '/assets/icons/achievement5.svg', unlocked: false },
  { id: 6, src: '/assets/icons/achievement6.svg', unlocked: false },
];

export default function AchievementsCard() {
  return (
    <div className="achievements-card">
      <div className="achievements-card__content">
        {/* Заголовок + divider */}
        <div className="achievements-card__header">
          <h3 className="achievements-card__title">ACHIEVEMENTS</h3>
          <div className="achievements-card__line" />
        </div>

        {/* Слоты ачивок */}
        <div className="achievements-card__slots">
          {ACHIEVEMENTS.map((ach) => (
            <div
              key={ach.id}
              className={`achievements-card__slot ${ach.unlocked ? 'achievements-card__slot--unlocked' : 'achievements-card__slot--locked'}`}
            >
              <img className="achievements-card__slot-icon" src={ach.src} alt="" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
