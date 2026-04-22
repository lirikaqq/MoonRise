import React from 'react';
import './StatsTopRow.css';

const ROLE_ICONS = {
  tank: '/assets/icons/icon-role-tank.svg',
  dps: '/assets/icons/icon-role-dps.svg',
  sup: '/assets/icons/icon-role-sup.svg',
};

export default function StatsTopRow({ stats }) {
  const role = stats?.role || 'tank';
  const roleIconSrc = ROLE_ICONS[role] || ROLE_ICONS.tank;

  return (
    <div className="stats-top-row">
      {/* 12 PLACE */}
      <div className="stat-card-small">
        <div className="stat-card-small__accent-line" />
        <div className="stat-card-place__content">
          <div className="stat-card-place__number">{stats?.place || '12'}</div>
          <div className="stat-card-place__label">PLACE</div>
        </div>
      </div>

      {/* ROLE (TANK/DPS/SUP) */}
      <div className="stat-card-small">
        <div className="stat-card-small__accent-line" />
        <div className="stat-card-role__content">
          <img className="stat-card-role__icon" src={roleIconSrc} alt={role} />
          <div className="stat-card-role__text">{role.toUpperCase()}</div>
        </div>
      </div>

      {/* MVP SCORE */}
      <div className="stat-card-small">
        <div className="stat-card-small__accent-line" />
        <div className="stat-card-score__content">
          <div className="stat-card-score__label stat-card-score__label--accent">MVP<br/>SCORE</div>
          <div className="stat-card-score__right">
            <div className="stat-card-score__value">{stats?.mvpScore || '24.28'}</div>
            <div className="stat-card-score__sub">{stats?.mvpFrom || '20 FROM 100'}</div>
          </div>
        </div>
      </div>

      {/* SVP SCORE */}
      <div className="stat-card-small">
        <div className="stat-card-small__accent-line" />
        <div className="stat-card-score__content">
          <div className="stat-card-score__label stat-card-score__label--accent">SVP<br/>SCORE</div>
          <div className="stat-card-score__right">
            <div className="stat-card-score__value">{stats?.svpScore || '3.44'}</div>
            <div className="stat-card-score__sub">{stats?.svpFrom || '28 FROM 220'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
