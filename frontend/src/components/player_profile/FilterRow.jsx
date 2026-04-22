import React from 'react';
import './FilterRow.css';

export default function FilterRow({ tournament, stats }) {
  return (
    <div className="filter-row">
      {/* Dropdown */}
      <div className="filter-row__dropdown">
        <span className="filter-row__dropdown-text">{tournament || 'MOONRISE MIX VOL. 3'}</span>
        <img className="filter-row__dropdown-icon" src="/assets/icons/tournament_filter.svg" alt="" />
      </div>

      {/* Playtime */}
      <div className="filter-row__playtime">
        <img className="filter-row__playtime-icon" src="/assets/icons/playtime.svg" alt="" />
        <span className="filter-row__playtime-text">{stats?.playtime || '3.6H PLAYTIME'}</span>
      </div>

      {/* Maps */}
      <div className="filter-row__maps">
        <img className="filter-row__maps-icon" src="/assets/icons/maps.svg" alt="" />
        <span className="filter-row__maps-text">{stats?.maps || '10 MAPS'}</span>
      </div>

      {/* Win/Lose */}
      <div className="filter-row__winlose">
        <div className="filter-row__win">{stats?.wins || '8'} WIN</div>
        <div className="filter-row__lose">{stats?.losses || '2'} LOSE</div>
      </div>
    </div>
  );
}
