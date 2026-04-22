import React from 'react';
import './DivisionsCard.css';

const DIVISIONS = [
  { role: 'TANK', level: 6, roleIcon: '/assets/icons/icon-role-tank.svg', iconPath: '/assets/icons/div6_Images/div6_ImgID1.png' },
  { role: 'DPS', level: 14, roleIcon: '/assets/icons/icon-role-dps.svg', iconPath: '/assets/icons/div14_Images/div14_ImgID1.png' },
  { role: 'SUP', level: 14, roleIcon: '/assets/icons/icon-role-sup.svg', iconPath: '/assets/icons/div14_Images/div14_ImgID1.png' },
];

export default function DivisionsCard() {
  return (
    <div className="divisions-card">
      {/* Контент поверх обводки */}
      <div className="divisions-card__content">
        {/* Заголовок + divider */}
        <div className="divisions-card__header">
          <h3 className="divisions-card__title">DIVISIONS</h3>
          <div className="divisions-card__line" />
        </div>

        {/* 3 блока: TANK / DPS / SUP */}
        <div className="divisions-card__blocks">
          {DIVISIONS.map((div) => (
            <div key={div.role} className="divisions-card__block">
              <div className="divisions-card__icon">
                <img
                  src={div.iconPath}
                  alt={`Division ${div.level} ${div.role}`}
                />
              </div>
              <div className="divisions-card__label">
                <img
                  className="divisions-card__role-icon"
                  src={div.roleIcon}
                  alt={div.role}
                />
                {div.role}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
