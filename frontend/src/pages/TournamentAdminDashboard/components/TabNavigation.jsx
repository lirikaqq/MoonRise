import { useMemo } from 'react';
import './TabNavigation.css';

const TabNavigation = ({ tabs, activeTab, onTabChange }) => {
  const activeIndex = useMemo(() => 
    tabs.findIndex(tab => tab.key === activeTab), 
    [tabs, activeTab]
  );

  return (
    <div className="tab-navigation">
      <div className="tab-list">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-item ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => onTabChange(tab.key)}
          >
            <span className="tab-icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Подчёркивание активной вкладки */}
      <div 
        className="tab-indicator"
        style={{
          transform: `translateX(${activeIndex * 100}%)`,
        }}
      />
    </div>
  );
};

export default TabNavigation;