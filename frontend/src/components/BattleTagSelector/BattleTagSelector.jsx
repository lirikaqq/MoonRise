import { useState } from 'react';
import './BattleTagSelector.css';

export default function BattleTagSelector({
  userBattletags = [],
  selectedBattletagId = null,
  newBattletag = null,
  onSelectExisting,
  onAddNew,
  onRemoveNew,
  disabled = false,
  error = null,
}) {
  const [mode, setMode] = useState('existing');
  const [inputValue, setInputValue] = useState('');

  const validateBattletagFormat = (tag) => {
    // Формат: Имя#12345 (разрешаем латиницу, цифры, от 3 до 12 символов до решетки)
    const regex = /^[a-zA-Z0-9]{3,12}#[0-9]{4,5}$/;
    return regex.test(tag);
  };

  const handleAddNew = (e) => {
    e.preventDefault(); // ВАЖНО: предотвращает отправку всей формы!
    if (!inputValue.trim()) return;
    if (!validateBattletagFormat(inputValue)) return;
    onAddNew(inputValue);
  };

  return (
    <div className="battletag-selector">
      <label>
        <span className="required">*</span> BATTLETAG
      </label>

      <div className="mode-tabs">
        <button
          type="button"
          className={`mode-tab font-palui ${mode === 'existing' ? 'active' : ''}`}
          onClick={() => setMode('existing')}
          disabled={disabled}
        >
          ВЫБРАТЬ ИЗ ПРОФИЛЯ
        </button>
        <button
          type="button"
          className={`mode-tab font-palui ${mode === 'new' ? 'active' : ''}`}
          onClick={() => setMode('new')}
          disabled={disabled}
        >
          ДОБАВИТЬ НОВЫЙ
        </button>
      </div>

      {mode === 'existing' && (
        <div className="mode-content">
          {userBattletags.length === 0 ? (
            <p className="no-battletags font-ponter">
              У вас нет сохранённых BattleTag. Переключитесь на "Добавить новый".
            </p>
          ) : (
            <select
              value={selectedBattletagId || ''}
              onChange={(e) => onSelectExisting(parseInt(e.target.value))}
              disabled={disabled}
              className={error ? 'input-error font-ponter' : 'font-ponter'}
            >
              <option value="">ВЫБЕРИТЕ BATTLETAG...</option>
              {userBattletags.map((bt) => (
                <option key={bt.id} value={bt.id}>
                  {bt.tag} {bt.is_primary ? '(основной)' : ''}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {mode === 'new' && (
        <div className="mode-content">
          <div className="input-group">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Name#12345"
              disabled={disabled}
              className={error ? 'input-error font-ponter' : 'font-ponter'}
            />
            <button
              type="button"
              onClick={handleAddNew}
              disabled={disabled || !validateBattletagFormat(inputValue)}
              className="btn-add font-palui"
            >
              + ДОБАВИТЬ
            </button>
          </div>
          <p className="hint font-ponter">Формат: Name#12345 (латиница/цифры, знак #, 4-5 цифр)</p>
        </div>
      )}

      {/* Отображение выбранного нового тега */}
      {newBattletag && mode === 'new' && (
        <div className="selected-tag font-ponter">
          <span>✓ Будет добавлен: <strong>{newBattletag}</strong></span>
          <button
            type="button"
            onClick={onRemoveNew}
            disabled={disabled}
            className="btn-remove"
          >
            ✕
          </button>
        </div>
      )}

      {/* Ошибки валидации */}
      {error && <div className="form-error font-ponter">{error}</div>}
    </div>
  );
}