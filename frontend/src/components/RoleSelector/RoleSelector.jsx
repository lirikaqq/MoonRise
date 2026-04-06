// frontend/src/components/RoleSelector/RoleSelector.jsx

import React from 'react';
import './RoleSelector.css';

const ROLES = [
  { value: 'tank', label: '🛡️ Tank' },
  { value: 'dps', label: '⚔️ DPS' },
  { value: 'support', label: '💊 Support' },
  { value: 'flex', label: '🔄 Flex' },
];

export default function RoleSelector({
  primaryRole,
  secondaryRole,
  onPrimaryChange,
  onSecondaryChange,
  disabled = false,
  error = null,
}) {
  return (
    <div className="role-selector">
      <div className="role-group">
        <label htmlFor="primary-role">
          <span className="required">*</span> Основная роль
        </label>
        <select
          id="primary-role"
          value={primaryRole || ''}
          onChange={(e) => onPrimaryChange(e.target.value)}
          disabled={disabled}
          className={error ? 'input-error' : ''}
        >
          <option value="">Выберите роль...</option>
          {ROLES.map((role) => (
            <option key={role.value} value={role.value}>
              {role.label}
            </option>
          ))}
        </select>
      </div>

      <div className="role-group">
        <label htmlFor="secondary-role">
          <span className="required">*</span> Дополнительная роль
        </label>
        <select
          id="secondary-role"
          value={secondaryRole || ''}
          onChange={(e) => onSecondaryChange(e.target.value)}
          disabled={disabled}
          className={error ? 'input-error' : ''}
        >
          <option value="">Выберите роль...</option>
          {ROLES.map((role) => (
            <option
              key={role.value}
              value={role.value}
              disabled={primaryRole === role.value}
            >
              {role.label}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="form-error">{error}</div>}
    </div>
  );
}