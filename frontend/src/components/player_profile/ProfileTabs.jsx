import React, { useState } from 'react';
import './ProfileTabs.css';

const TABS = [
  { id: 'overview', label: 'OVERVIEW' },
  { id: 'tournaments', label: 'TOURNAMENTS' },
  { id: 'achievements', label: 'ACHIEVEMENTS' },
];

export default function ProfileTabs({ activeTab, onTabChange }) {
  return (
    <div>
      <div className="profile-tabs" style={{ position: 'relative', left: '-3px', top: '17px' }}>
        {TABS.map((tab) => (
          <div
            key={tab.id}
            className={`profile-tab ${activeTab === tab.id ? 'profile-tab--active' : ''}`}
            onClick={() => onTabChange(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
          >
            {tab.label}
          </div>
        ))}
      </div>
      <hr className="profile-tabs__line" />
    </div>
  );
}
