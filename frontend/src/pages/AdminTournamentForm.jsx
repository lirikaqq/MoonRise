import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { tournamentsApi } from '../api/tournaments';
import { createStage } from '../api/stages';
import DescriptionEditor from '../components/admin/DescriptionEditor';
import StageBuilder from '../components/stages/StageBuilder';
import './AdminTournamentForm.css';

const FORMAT_OPTIONS = [
  { value: 'draft', label: 'Draft' },
  { value: 'mix', label: 'Mix' },
];

const STATUS_OPTIONS = [
  { value: 'upcoming', label: 'Upcoming' },
  { value: 'registration', label: 'Registration' },
  { value: 'checkin', label: 'Check-in' },
  { value: 'draft', label: 'Draft' },
  { value: 'ongoing', label: 'Ongoing' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const STRUCTURE_OPTIONS = [
  { value: 'SINGLE_ELIMINATION', label: 'Single Elimination' },
  { value: 'DOUBLE_ELIMINATION', label: 'Double Elimination' },
  { value: 'ROUND_ROBIN', label: 'Round-Robin' },
  { value: 'GROUPS_PLUS_PLAYOFF', label: 'Groups + Playoff' },
  { value: 'SWISS', label: 'Swiss System' },
];

const TEAM_PRESETS = [
  { label: '5v5', size: 5, limits: { tank: 1, dps: 2, sup: 2, flex: 0 } },
  { label: '6v6', size: 6, limits: { tank: 2, dps: 2, sup: 2, flex: 0 } },
  { label: '4v4', size: 4, limits: { tank: 1, dps: 1, sup: 1, flex: 1 } },
  { label: '3v3', size: 3, limits: { tank: 1, dps: 1, sup: 1, flex: 0 } },
];

const RECOMMENDED_COVER = { width: 1200, height: 630 };

function Section({ title, children, defaultOpen = true, hint }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="atf-section">
      <button type="button" className="atf-section-header" onClick={() => setOpen(!open)}>
        <div>
          <span className="atf-section-title">{title}</span>
          {hint && <span className="atf-section-hint">{hint}</span>}
        </div>
        <span className={`atf-section-arrow ${open ? 'open' : ''}`}>▼</span>
      </button>
      {open && <div className="atf-section-body">{children}</div>}
    </div>
  );
}

function FormInput({ label, name, children, required, hint }) {
  return (
    <div className="atf-field">
      <label htmlFor={name} className="atf-field-label">
        {label} {required && <span className="atf-required">*</span>}
      </label>
      {children}
      {hint && <p className="atf-hint">{hint}</p>}
    </div>
  );
}

export default function AdminTournamentForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [tournament, setTournament] = useState({
    title: '',
    format: 'mix',
    status: 'upcoming',
    start_date: '',
    end_date: '',
    max_participants: 64,
    cover_url: '',
    registration_open: '',
    registration_close: '',
    checkin_open: '',
    checkin_close: '',
    is_featured: false,
    structure_type: 'SINGLE_ELIMINATION',
    structure_settings: {},
    twitch_channel: '',
    rules_url: '',
    description_general: '',
    description_dates: '',
    description_requirements: '',
    team_config: {
      team_size: 6,
      role_limits: { tank: 2, dps: 2, sup: 2, flex: 0 }
    },
  });

  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationError, setValidationError] = useState('');
  const [stages, setStages] = useState([{
    stage_number: 1,
    name: 'Основной этап',
    format: 'ROUND_ROBIN',
    settings: {
      stage_config: { points_per_win: 3, points_per_draw: 1, points_per_loss: 0 },
      advancement_config: null
    }
  }]);

  const progress = useMemo(() => {
    let filled = 0;
    const total = 7;
    if (tournament.title?.trim()) filled++;
    if (tournament.start_date && tournament.end_date) filled++;
    if (tournament.team_config?.team_size) filled++;
    if (tournament.description_general?.trim()) filled++;
    if (tournament.structure_type) filled++;
    if (coverPreview || tournament.cover_url) filled++;
    if (Object.keys(tournament.team_config?.role_limits || {}).length > 0) filled++;
    return Math.round((filled / total) * 100);
  }, [tournament, coverPreview]);

  useEffect(() => {
    if (isEditing) {
      setLoading(true);
      tournamentsApi.getById(id)
        .then(data => {
          const fmt = (dt) => dt ? new Date(dt).toISOString().slice(0, 16) : '';
          setTournament({
            ...data,
            start_date: fmt(data.start_date),
            end_date: fmt(data.end_date),
            registration_open: fmt(data.registration_open),
            registration_close: fmt(data.registration_close),
            checkin_open: fmt(data.checkin_open),
            checkin_close: fmt(data.checkin_close),
            structure_settings: data.structure_settings || {},
            twitch_channel: data.twitch_channel || '',
            rules_url: data.rules_url || '',
            description_general: data.description_general || '',
            description_dates: data.description_dates || '',
            description_requirements: data.description_requirements || '',
            team_config: data.team_config || {
              team_size: 6,
              role_limits: { tank: 2, dps: 2, sup: 2, flex: 0 }
            },
          });
          if (data.cover_url) setCoverPreview(data.cover_url);
        })
        .catch(() => setError('Не удалось загрузить данные турнира.'))
        .finally(() => setLoading(false));
    }
  }, [id, isEditing]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTournament(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleDescriptionChange = (field) => (html) => {
    setTournament(prev => ({ ...prev, [field]: html }));
  };

  const handleCoverChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setCoverFile(file);
    setCoverPreview(URL.createObjectURL(file));
  };

  const handleTeamSizeChange = (size) => {
    const newSize = parseInt(size, 10) || 6;
    const currentLimits = tournament.team_config?.role_limits || { tank: 2, dps: 2, sup: 2, flex: 0 };
    const base = Math.floor(newSize / 3);
    const newLimits = {
      tank: base,
      dps: base + (newSize % 3 > 0 ? 1 : 0),
      sup: base,
      flex: Math.max(0, newSize - base * 3 - (newSize % 3 > 0 ? 1 : 0))
    };
    setTournament(prev => ({
      ...prev,
      team_config: { team_size: newSize, role_limits: newLimits }
    }));
    setValidationError('');
  };

  const handleRoleLimitChange = (role, value) => {
    const numValue = parseInt(value, 10) || 0;
    setTournament(prev => ({
      ...prev,
      team_config: {
        ...prev.team_config,
        role_limits: {
          ...(prev.team_config?.role_limits || {}),
          [role]: numValue
        }
      }
    }));
    setValidationError('');
  };

  const applyPreset = (preset) => {
    setTournament(prev => ({
      ...prev,
      team_config: {
        team_size: preset.size,
        role_limits: { ...preset.limits }
      }
    }));
    setValidationError('');
  };

  const calculateTotalRoles = (limits = {}) => {
    return Object.values(limits).reduce((sum, val) => sum + (val || 0), 0);
  };

  const validateTeamConfig = () => {
    const config = tournament.team_config || {};
    const total = calculateTotalRoles(config.role_limits);
    if (total === 0) {
      setValidationError("Сумма ролей не может быть 0");
      return false;
    }
    if (total !== config.team_size) {
      setValidationError(`Сумма ролей (${total}) должна равняться Team Size (${config.team_size})`);
      return false;
    }
    setValidationError('');
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateTeamConfig()) return;

    setLoading(true);
    setError('');
    setValidationError('');

    const toISO = (dt) => dt ? new Date(dt).toISOString() : null;

    let structureSettings = null;
    const st = tournament.structure_type;
    if (st === 'GROUPS_PLUS_PLAYOFF') {
      structureSettings = {
        num_groups: 4,
        teams_per_group_to_playoff: 2,
      };
    } else if (st === 'SWISS') {
      structureSettings = { num_swiss_rounds: 5 };
    } else if (st === 'DOUBLE_ELIMINATION') {
      structureSettings = { enable_lower_bracket: true };
    }

    const dataToSend = {
      title: tournament.title,
      format: tournament.format,
      status: tournament.status,
      start_date: toISO(tournament.start_date),
      end_date: toISO(tournament.end_date),
      registration_open: toISO(tournament.registration_open),
      registration_close: toISO(tournament.registration_close),
      checkin_open: toISO(tournament.checkin_open),
      checkin_close: toISO(tournament.checkin_close),
      max_participants: parseInt(tournament.max_participants, 10),
      cover_url: coverFile ? coverPreview : tournament.cover_url || null,
      is_featured: tournament.is_featured,
      structure_type: tournament.structure_type,
      structure_settings: structureSettings,
      twitch_channel: tournament.twitch_channel || null,
      rules_url: tournament.rules_url || null,
      description_general: tournament.description_general || null,
      description_dates: tournament.description_dates || null,
      description_requirements: tournament.description_requirements || null,
      team_config: tournament.team_config,
    };

    try {
      let tournamentId = id;
      if (isEditing) {
        await tournamentsApi.update(id, dataToSend);
      } else {
        const created = await tournamentsApi.create(dataToSend);
        tournamentId = created.id;
        if (stages && stages.length > 0) {
          for (const stage of stages) {
            await createStage({
              tournament_id: tournamentId,
              stage_number: stage.stage_number,
              name: stage.name,
              format: stage.format,
              settings: stage.settings || null,
            });
          }
        }
      }
      navigate('/admin/tournaments');
    } catch (err) {
      const errorDetail = err.response?.data?.detail;
      setError(typeof errorDetail === 'string' ? errorDetail : 'Произошла ошибка при сохранении');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const currentTotalRoles = calculateTotalRoles(tournament.team_config?.role_limits);
  const isTeamConfigValid = currentTotalRoles === (tournament.team_config?.team_size || 0);

  if (loading && isEditing) return <div className="atf-loading">Loading Tournament...</div>;

  return (
    <div className="atf-page">
      <div className="atf-header">
        <h1 className="atf-title">{isEditing ? 'Редактирование турнира' : 'Создание нового турнира'}</h1>
        <div className="atf-progress-container">
          <div className="atf-progress-bar" style={{ width: `${progress}%` }} />
          <span className="atf-progress-text">{progress}% заполнено</span>
        </div>
      </div>

      {error && <div className="atf-error">{error}</div>}
      {validationError && <div className="atf-error" style={{ backgroundColor: '#ff4444' }}>{validationError}</div>}

      <div className="atf-layout">
        <div className="atf-form-col">
          <form onSubmit={handleSubmit} className="atf-form">

            <Section title="📌 Основные настройки" defaultOpen={true}>
              <div className="atf-grid-2">
                <FormInput label="Название турнира" required>
                  <input type="text" name="title" value={tournament.title} onChange={handleChange} required className="atf-input" placeholder="MoonRise Mix Vol. 4" />
                </FormInput>
                <FormInput label="Максимум участников" required>
                  <input type="number" name="max_participants" value={tournament.max_participants} onChange={handleChange} required min="8" className="atf-input" />
                </FormInput>
              </div>

              <div className="atf-grid-3">
                <FormInput label="Формат" required>
                  <select name="format" value={tournament.format} onChange={handleChange} className="atf-select">
                    {FORMAT_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                  </select>
                </FormInput>
                <FormInput label="Статус" required>
                  <select name="status" value={tournament.status} onChange={handleChange} className="atf-select">
                    {STATUS_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                  </select>
                </FormInput>
                <FormInput label="Featured">
                  <label className="atf-checkbox-label">
                    <input type="checkbox" name="is_featured" checked={tournament.is_featured} onChange={handleChange} />
                    <span>Отображать на главной</span>
                  </label>
                </FormInput>
              </div>
            </Section>

            <Section title="👥 Team Configuration" defaultOpen={true}>
              <div className="atf-grid-2">
                <FormInput label="Team Size" required hint="Количество игроков в одной команде">
                  <input
                    type="number"
                    value={tournament.team_config?.team_size || 6}
                    onChange={(e) => handleTeamSizeChange(e.target.value)}
                    min="3"
                    max="7"
                    className="atf-input"
                  />
                </FormInput>

                <div className="atf-field">
                  <label className="atf-field-label">Быстрые пресеты</label>
                  <div className="atf-presets">
                    {TEAM_PRESETS.map(preset => (
                      <button
                        key={preset.label}
                        type="button"
                        className="atf-preset-btn"
                        onClick={() => applyPreset(preset)}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <FormInput label={`Лимиты по ролям (сейчас: ${currentTotalRoles} / ${tournament.team_config?.team_size || 6})`}>
                <div className="atf-role-limits-grid">
                  {['tank', 'dps', 'sup', 'flex'].map(role => (
                    <div key={role} className="atf-role-item">
                      <label>{role.toUpperCase()}</label>
                      <input
                        type="number"
                        value={tournament.team_config?.role_limits?.[role] || 0}
                        onChange={(e) => handleRoleLimitChange(role, e.target.value)}
                        min="0"
                        max="6"
                        className="atf-input-small"
                      />
                    </div>
                  ))}
                </div>
                {!isTeamConfigValid && (
                  <p className="atf-error-text">Сумма ролей должна равняться Team Size</p>
                )}
              </FormInput>
            </Section>

            <Section title="🖼️ Обложка" defaultOpen={false}>
              <FormInput label="Обложка турнира">
                <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleCoverChange} className="atf-file-input" />
                <p className="atf-hint">
                  Рекомендуемый размер: {RECOMMENDED_COVER.width}×{RECOMMENDED_COVER.height} px (JPG, PNG, WebP)
                </p>
              </FormInput>
              {coverPreview && (
                <div className="atf-cover-preview">
                  <img src={coverPreview} alt="Preview" />
                </div>
              )}
            </Section>

            <Section title="📝 Описание турнира">
              <div>
                <label className="atf-editor-label">Общая информация</label>
                <DescriptionEditor value={tournament.description_general} onChange={handleDescriptionChange('description_general')} />
              </div>
              <div>
                <label className="atf-editor-label">Даты и формат проведения</label>
                <DescriptionEditor value={tournament.description_dates} onChange={handleDescriptionChange('description_dates')} />
              </div>
              <div>
                <label className="atf-editor-label">Требования к участникам</label>
                <DescriptionEditor value={tournament.description_requirements} onChange={handleDescriptionChange('description_requirements')} />
              </div>
            </Section>

            <Section title="🏆 Этапы и структура" defaultOpen={false}>
              <StageBuilder stages={stages} onChange={setStages} />
            </Section>

            <Section title="📅 Даты и тайминги" defaultOpen={false}>
              <div className="atf-grid-2">
                <FormInput label="Дата начала" required>
                  <input type="datetime-local" name="start_date" value={tournament.start_date} onChange={handleChange} required className="atf-input" />
                </FormInput>
                <FormInput label="Дата окончания" required>
                  <input type="datetime-local" name="end_date" value={tournament.end_date} onChange={handleChange} required className="atf-input" />
                </FormInput>
              </div>
              <div className="atf-grid-2">
                <FormInput label="Начало регистрации">
                  <input type="datetime-local" name="registration_open" value={tournament.registration_open || ''} onChange={handleChange} className="atf-input" />
                </FormInput>
                <FormInput label="Конец регистрации">
                  <input type="datetime-local" name="registration_close" value={tournament.registration_close || ''} onChange={handleChange} className="atf-input" />
                </FormInput>
              </div>
              <div className="atf-grid-2">
                <FormInput label="Начало чек-ина">
                  <input type="datetime-local" name="checkin_open" value={tournament.checkin_open || ''} onChange={handleChange} className="atf-input" />
                </FormInput>
                <FormInput label="Конец чек-ина">
                  <input type="datetime-local" name="checkin_close" value={tournament.checkin_close || ''} onChange={handleChange} className="atf-input" />
                </FormInput>
              </div>
            </Section>

            <Section title="📺 Трансляция и регламент" defaultOpen={false}>
              <FormInput label="Twitch канал" hint="Для встроенной трансляции">
                <input type="text" name="twitch_channel" value={tournament.twitch_channel || ''} onChange={handleChange} className="atf-input" placeholder="username" />
              </FormInput>
              <FormInput label="Ссылка на регламент" hint="Google Doc, PDF или сайт">
                <input type="url" name="rules_url" value={tournament.rules_url || ''} onChange={handleChange} className="atf-input" placeholder="https://docs.google.com/..." />
              </FormInput>
            </Section>

            <div className="atf-actions">
              <Link to="/admin/tournaments" className="atf-btn atf-btn-secondary">Отмена</Link>
              <button type="submit" disabled={loading || !isTeamConfigValid} className="atf-btn atf-btn-primary">
                {loading ? 'Сохранение...' : isEditing ? 'Обновить турнир' : 'Создать турнир'}
              </button>
            </div>
          </form>
        </div>

        <div className="atf-preview-col">
          <div className="atf-preview-label">ПРЕВЬЮ</div>
          <div className="atf-preview-card">
            {coverPreview ? (
              <div className="atf-preview-cover">
                <img src={coverPreview} alt="Cover preview" />
              </div>
            ) : (
              <div className="atf-preview-cover-placeholder">Обложка не выбрана</div>
            )}
            <div className="atf-preview-info">
              <h2 className="atf-preview-title" style={{ fontFamily: 'Ponter' }}>
                {tournament.title || 'НАЗВАНИЕ ТУРНИРА'}
              </h2>
              <div className="atf-preview-meta" style={{ fontFamily: 'Digits' }}>
                {tournament.start_date && tournament.end_date ? (
                  <span>{new Date(tournament.start_date).toLocaleDateString('ru-RU')} — {new Date(tournament.end_date).toLocaleDateString('ru-RU')}</span>
                ) : (
                  <span>Date TBD</span>
                )}
                <span className="atf-preview-format">{tournament.format?.toUpperCase() || 'MIX'}</span>
              </div>
            </div>

            {tournament.description_general && (
              <div className="atf-preview-description">
                <h4 style={{ fontFamily: 'Ponter', color: 'var(--accent)', margin: '12px 0 6px', fontSize: '0.85rem' }}>ОБЩАЯ ИНФОРМАЦИЯ</h4>
                <div style={{ fontFamily: 'Montserrat', fontSize: '12px', lineHeight: '1.5' }} dangerouslySetInnerHTML={{ __html: tournament.description_general }} />
              </div>
            )}
            {tournament.description_dates && (
              <div className="atf-preview-description">
                <h4 style={{ fontFamily: 'Ponter', color: 'var(--accent)', margin: '12px 0 6px', fontSize: '0.85rem' }}>ДАТЫ ПРОВЕДЕНИЯ</h4>
                <div style={{ fontFamily: 'Montserrat', fontSize: '12px', lineHeight: '1.5' }} dangerouslySetInnerHTML={{ __html: tournament.description_dates }} />
              </div>
            )}
            {tournament.description_requirements && (
              <div className="atf-preview-description">
                <h4 style={{ fontFamily: 'Ponter', color: 'var(--accent)', margin: '12px 0 6px', fontSize: '0.85rem' }}>ТРЕБОВАНИЯ</h4>
                <div style={{ fontFamily: 'Montserrat', fontSize: '12px', lineHeight: '1.5' }} dangerouslySetInnerHTML={{ __html: tournament.description_requirements }} />
              </div>
            )}

            {tournament.twitch_channel && (
              <div className="atf-preview-twitch">
                📺 twitch.tv/{tournament.twitch_channel}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}