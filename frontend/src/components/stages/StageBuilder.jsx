import React, { useState } from 'react';
import './StageBuilder.css';

const STAGE_FORMATS = [
  { value: 'ROUND_ROBIN', label: 'Round Robin (Каждый с каждым)' },
  { value: 'SWISS', label: 'Швейцарская система' },
  { value: 'SINGLE_ELIMINATION', label: 'Single Elimination' },
  { value: 'DOUBLE_ELIMINATION', label: 'Double Elimination' },
];

const SEEDING_RULES = [
  { value: 'UPPER_LOWER_SPLIT', label: 'Разделение на верх/низ' },
  { value: 'CROSS_GROUP_SEEDING', label: 'Перекрестный посев (A1 vs B2)' },
];

/**
 * Конструктор этапов турнира.
 * Позволяет добавлять, удалять и настраивать этапы.
 */
export default function StageBuilder({ stages = [], onChange }) {
  const [localStages, setLocalStages] = useState(stages.length > 0 ? stages : [createDefaultStage()]);

  // При изменении локальных данных уведомляем родителя
  React.useEffect(() => {
    if (onChange) {
      onChange(localStages);
    }
  }, [localStages, onChange]);

  const addStage = () => {
    const newStage = createDefaultStage(localStages.length + 1);
    setLocalStages([...localStages, newStage]);
  };

  const removeStage = (index) => {
    if (localStages.length <= 1) {
      alert('Нельзя удалить последний этап!');
      return;
    }
    const newStages = localStages.filter((_, i) => i !== index);
    // Перенумеровываем
    newStages.forEach((s, i) => s.stage_number = i + 1);
    setLocalStages(newStages);
  };

  const updateStage = (index, field, value) => {
    const newStages = [...localStages];
    newStages[index] = { ...newStages[index], [field]: value };

    // Если меняется формат, сбрасем настройки
    if (field === 'format') {
      newStages[index].settings = {
        stage_config: getDefaultStageConfig(value),
        advancement_config: newStages[index].settings?.advancement_config || null
      };
    }

    setLocalStages(newStages);
  };

  const updateStageSettings = (index, settingsKey, settingsValue) => {
    const newStages = [...localStages];
    newStages[index] = {
      ...newStages[index],
      settings: {
        ...newStages[index].settings,
        [settingsKey]: settingsValue
      }
    };
    setLocalStages(newStages);
  };

  const updateAdvancementConfig = (index, advField, value) => {
    const newStages = [...localStages];
    const advConfig = newStages[index].settings?.advancement_config || {};
    newStages[index] = {
      ...newStages[index],
      settings: {
        ...newStages[index].settings,
        advancement_config: { ...advConfig, [advField]: value }
      }
    };
    setLocalStages(newStages);
  };

  const hasStageSettings = (index) => {
    // Настройки перехода появляются только если есть следующий этап
    return index < localStages.length - 1;
  };

  return (
    <div className="stage-builder">
      <h3 className="stage-builder-title">Конструктор этапов</h3>

      {localStages.map((stage, index) => (
        <div key={index} className="stage-card">
          <div className="stage-card-header">
            <span className="stage-number">Этап {stage.stage_number}</span>
            <input
              type="text"
              value={stage.name}
              onChange={(e) => updateStage(index, 'name', e.target.value)}
              placeholder="Название этапа"
              className="stage-name-input"
            />
            {localStages.length > 1 && (
              <button
                type="button"
                onClick={() => removeStage(index)}
                className="stage-remove-btn"
              >
                ✕
              </button>
            )}
          </div>

          <div className="stage-card-body">
            <div className="stage-field">
              <label>Формат:</label>
              <select
                value={stage.format}
                onChange={(e) => updateStage(index, 'format', e.target.value)}
                className="stage-select"
              >
                {STAGE_FORMATS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            {/* Настройки этапа */}
            <div className="stage-section">
              <h4>Настройки этапа</h4>
              <div className="stage-field">
                <label>Очки за победу:</label>
                <input
                  type="number"
                  value={stage.settings?.stage_config?.points_per_win || 3}
                  onChange={(e) => updateStageSettings(index, 'stage_config', {
                    ...stage.settings?.stage_config,
                    points_per_win: parseInt(e.target.value)
                  })}
                  className="stage-input"
                />
              </div>
              <div className="stage-field">
                <label>Очки за ничью:</label>
                <input
                  type="number"
                  value={stage.settings?.stage_config?.points_per_draw || 1}
                  onChange={(e) => updateStageSettings(index, 'stage_config', {
                    ...stage.settings?.stage_config,
                    points_per_draw: parseInt(e.target.value)
                  })}
                  className="stage-input"
                />
              </div>
              <div className="stage-field">
                <label>Очки за поражение:</label>
                <input
                  type="number"
                  value={stage.settings?.stage_config?.points_per_loss || 0}
                  onChange={(e) => updateStageSettings(index, 'stage_config', {
                    ...stage.settings?.stage_config,
                    points_per_loss: parseInt(e.target.value)
                  })}
                  className="stage-input"
                />
              </div>
            </div>

            {/* Настройки перехода (только если есть следующий этап) */}
            {hasStageSettings(index) && (
              <div className="stage-section advancement-section">
                <h4>Правила перехода к следующему этапу</h4>

                <div className="stage-field">
                  <label>Команд выходит из группы:</label>
                  <input
                    type="number"
                    value={stage.settings?.advancement_config?.participants_to_advance_per_group || 4}
                    onChange={(e) => updateAdvancementConfig(
                      index,
                      'participants_to_advance_per_group',
                      parseInt(e.target.value)
                    )}
                    className="stage-input"
                  />
                </div>

                <div className="stage-field">
                  <label>Правило распределения:</label>
                  <select
                    value={stage.settings?.advancement_config?.seeding_rule || ''}
                    onChange={(e) => updateAdvancementConfig(index, 'seeding_rule', e.target.value)}
                    className="stage-select"
                  >
                    <option value="">-- Выберите правило --</option>
                    {SEEDING_RULES.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                {/* UPPER_LOWER_SPLIT настройки */}
                {stage.settings?.advancement_config?.seeding_rule === 'UPPER_LOWER_SPLIT' && (
                  <>
                    <div className="stage-field">
                      <label>Места для верхней сетки (через запятую):</label>
                      <input
                        type="text"
                        placeholder="1, 2"
                        value={
                          (stage.settings?.advancement_config?.upper_bracket_ranks || [1, 2]).join(', ')
                        }
                        onChange={(e) => {
                          const ranks = e.target.value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
                          updateAdvancementConfig(index, 'upper_bracket_ranks', ranks);
                        }}
                        className="stage-input"
                      />
                    </div>
                    <div className="stage-field">
                      <label>Места для нижней сетки (через запятую):</label>
                      <input
                        type="text"
                        placeholder="3, 4"
                        value={
                          (stage.settings?.advancement_config?.lower_bracket_ranks || [3, 4]).join(', ')
                        }
                        onChange={(e) => {
                          const ranks = e.target.value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
                          updateAdvancementConfig(index, 'lower_bracket_ranks', ranks);
                        }}
                        className="stage-input"
                      />
                    </div>
                  </>
                )}

                {/* CROSS_GROUP_SEEDING настройки */}
                {stage.settings?.advancement_config?.seeding_rule === 'CROSS_GROUP_SEEDING' && (
                  <div className="stage-field">
                    <label>Формат следующего этапа:</label>
                    <p className="stage-hint">
                      Перекрестный посев: A1 vs B2, B1 vs A2
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}

      <button type="button" onClick={addStage} className="stage-add-btn">
        + Добавить этап
      </button>
    </div>
  );
}

function createDefaultStage(stageNumber = 1) {
  return {
    stage_number: stageNumber,
    name: `Этап ${stageNumber}`,
    format: 'ROUND_ROBIN',
    settings: {
      stage_config: {
        points_per_win: 3,
        points_per_draw: 1,
        points_per_loss: 0
      },
      advancement_config: null
    }
  };
}

function getDefaultStageConfig(format) {
  return {
    points_per_win: 3,
    points_per_draw: 1,
    points_per_loss: 0
  };
}
