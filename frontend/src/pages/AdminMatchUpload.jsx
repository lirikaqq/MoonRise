// frontend/src/pages/AdminMatchUpload.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getTournaments } from '../api/tournaments'
import {
  getTeamsByTournament,
  getEncountersByTournament,
  createTeam,
  createEncounter,
  uploadMatchLog,
} from '../api/matches'
import './AdminMatchUpload.css'

const STEP = {
  SELECT_TOURNAMENT:  1,
  SELECT_ENCOUNTER:   2,
  UPLOAD_FILE:        3,
  RESOLVE_CONFLICTS:  4,
  DONE:               5,
}

export default function AdminMatchUpload() {
  const navigate = useNavigate()

  const [step, setStep]                       = useState(STEP.SELECT_TOURNAMENT)
  const [tournaments, setTournaments]         = useState([])
  const [teams, setTeams]                     = useState([])
  const [encounters, setEncounters]           = useState([])
  const [selectedTournament, setSelectedTournament] = useState(null)
  const [selectedEncounter, setSelectedEncounter]   = useState(null)
  const [showCreateEncounter, setShowCreateEncounter] = useState(false)
  const [newEncounter, setNewEncounter]       = useState({
    team1_id: '', team2_id: '', stage: '', round_number: ''
  })
  const [showCreateTeam, setShowCreateTeam]   = useState(false)
  const [newTeamName, setNewTeamName]         = useState('')
  const [file, setFile]                       = useState(null)
  const [mapNumber, setMapNumber]             = useState('')
  const [conflicts, setConflicts]             = useState([])
  const [resolvedMappings, setResolvedMappings] = useState({})
  const [loading, setLoading]                 = useState(false)
  const [error, setError]                     = useState('')
  const [result, setResult]                   = useState(null)

  // Загружаем турниры при монтировании
  useEffect(() => {
    getTournaments()
      .then(setTournaments)
      .catch(() => setError('Не удалось загрузить турниры'))
  }, [])

  // Загружаем команды и встречи при выборе турнира
  useEffect(() => {
    if (!selectedTournament) return
    setLoading(true)
    Promise.all([
      getTeamsByTournament(selectedTournament.id),
      getEncountersByTournament(selectedTournament.id),
    ])
      .then(([t, e]) => { setTeams(t); setEncounters(e) })
      .catch(() => setError('Ошибка загрузки данных турнира'))
      .finally(() => setLoading(false))
  }, [selectedTournament])

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return
    setLoading(true)
    try {
      const team = await createTeam({
        name: newTeamName.trim(),
        tournament_id: selectedTournament.id,
      })
      setTeams(prev => [...prev, team])
      
      // ИСПРАВЛЕНИЕ UX: Автоматически подставляем команду в пустой слот!
      if (!newEncounter.team1_id) {
        setNewEncounter(p => ({ ...p, team1_id: team.id }))
      } else if (!newEncounter.team2_id) {
        setNewEncounter(p => ({ ...p, team2_id: team.id }))
      }

      setNewTeamName('')
      setShowCreateTeam(false)
    } catch {
      setError('Ошибка создания команды')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateEncounter = async () => {
    if (!newEncounter.team1_id || !newEncounter.team2_id)
      return setError('Выберите обе команды')
    if (newEncounter.team1_id === newEncounter.team2_id)
      return setError('Команды должны быть разными')

    setLoading(true)
    try {
      const enc = await createEncounter({
        tournament_id: selectedTournament.id,
        team1_id:      parseInt(newEncounter.team1_id),
        team2_id:      parseInt(newEncounter.team2_id),
        stage:         newEncounter.stage || null,
        round_number:  newEncounter.round_number
          ? parseInt(newEncounter.round_number)
          : null,
      })
      setEncounters(prev => [enc, ...prev])
      setSelectedEncounter(enc)
      setShowCreateEncounter(false)
      setNewEncounter({ team1_id: '', team2_id: '', stage: '', round_number: '' })
      setStep(STEP.UPLOAD_FILE)
    } catch {
      setError('Ошибка создания встречи')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (playerMappings = []) => {
    if (!file) return setError('Выберите файл')
    setLoading(true)
    setError('')
    try {
      const res = await uploadMatchLog({
        file,
        encounterId:    selectedEncounter.id,
        mapNumber:      mapNumber ? parseInt(mapNumber) : null,
        playerMappings,
      })

      if (res.status === 'ok') {
        setResult(res)
        setStep(STEP.DONE)
      } else if (res.status === 'duplicate') {
        setError(`⚠️ Этот лог уже загружен (Match ID: ${res.match_id})`)
      } else if (res.status === 'ambiguous') {
        setConflicts(res.conflicts)
        setResolvedMappings({})
        setStep(STEP.RESOLVE_CONFLICTS)
      }
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }

  const handleResolveAndUpload = () => {
    const unresolved = conflicts.filter(c => !resolvedMappings[c.player_name])
    if (unresolved.length > 0)
      return setError(
        `Не выбраны игроки: ${unresolved.map(c => c.player_name).join(', ')}`
      )

    const mappings = Object.entries(resolvedMappings)
      .filter(([, v]) => v !== 'skip')
      .map(([player_name, user_id]) => ({
        player_name,
        user_id: parseInt(user_id),
      }))

    handleUpload(mappings)
  }

  const getTeamName = id => teams.find(t => t.id === id)?.name ?? `Team ${id}`

  return (
    <div className="upload-page">
      <div className="upload-container">

        <div className="upload-header">
          <h1>Загрузка лога матча</h1>
          <p>Загрузите .txt файл Workshop-лога Overwatch</p>
        </div>

        <StepBar current={step} />

        {error && (
          <div className="error-message">
            <span>{error}</span>
            <button className="close-btn" onClick={() => setError('')}>
              закрыть
            </button>
          </div>
        )}

        {/* ШАГ 1: Выбор турнира */}
        {step === STEP.SELECT_TOURNAMENT && (
          <Card title="Шаг 1 — Выберите турнир">
            {loading ? <Spinner /> : (
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {tournaments.length === 0 && (
                  <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                    Турниры не найдены
                  </p>
                )}
                {tournaments.map(t => (
                  <button
                    key={t.id}
                    className="tournament-list-item"
                    onClick={() => {
                      setSelectedTournament(t)
                      setStep(STEP.SELECT_ENCOUNTER)
                      setError('')
                    }}
                  >
                    <div className="list-item-title">{t.title}</div>
                    <div className="list-item-subtitle">
                      {t.status} · {t.format}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* ШАГ 2: Выбор / создание встречи */}
        {step === STEP.SELECT_ENCOUNTER && (
          <Card
            title="Шаг 2 — Выберите встречу"
            subtitle={`Турнир: ${selectedTournament?.title}`}
            onBack={() => setStep(STEP.SELECT_TOURNAMENT)}
          >
            {loading ? <Spinner /> : (
              <>
                <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1rem' }}>
                  {encounters.length === 0 && (
                    <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                      Встреч пока нет. Создайте первую.
                    </p>
                  )}
                  {encounters.map(enc => (
                    <button
                      key={enc.id}
                      className="encounter-list-item"
                      onClick={() => {
                        setSelectedEncounter(enc)
                        setStep(STEP.UPLOAD_FILE)
                        setError('')
                      }}
                    >
                      <div className="list-item-title">
                        {getTeamName(enc.team1_id)}
                        <span style={{ color: '#a0aec0', margin: '0 0.5rem' }}>
                          vs
                        </span>
                        {getTeamName(enc.team2_id)}
                      </div>
                      <div className="list-item-subtitle">
                        {enc.stage && `${enc.stage} · `}
                        Счёт: {enc.team1_score}:{enc.team2_score} · {enc.matches?.length ?? 0} карт
                      </div>
                    </button>
                  ))}
                </div>

                {!showCreateEncounter ? (
                  <button
                    className="button link"
                    onClick={() => setShowCreateEncounter(true)}
                  >
                    + Создать новую встречу
                  </button>
                ) : (
                  <div className="sub-form">
                    <p className="title">Новая встреча</p>
                    <div className="form-grid">
                      <div>
                        <label className="form-label">Команда 1</label>
                        <select
                          value={newEncounter.team1_id}
                          className="select-field"
                          onChange={e =>
                            setNewEncounter(p => ({ ...p, team1_id: e.target.value }))
                          }
                        >
                          <option value="">Выбрать...</option>
                          {teams.map(t => (
                            <option key={t.id} value={t.id}>{t.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="form-label">Команда 2</label>
                        <select
                          value={newEncounter.team2_id}
                          className="select-field"
                          onChange={e =>
                            setNewEncounter(p => ({ ...p, team2_id: e.target.value }))
                          }
                        >
                          <option value="">Выбрать...</option>
                          {teams.map(t => (
                            <option key={t.id} value={t.id}>{t.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="form-grid">
                      <div>
                        <label className="form-label">Стадия (необязательно)</label>
                        <input
                          value={newEncounter.stage}
                          className="input-field"
                          onChange={e =>
                            setNewEncounter(p => ({ ...p, stage: e.target.value }))
                          }
                          placeholder="Group A / Playoffs"
                        />
                      </div>
                      <div>
                        <label className="form-label">Номер раунда</label>
                        <input
                          type="number"
                          value={newEncounter.round_number}
                          className="input-field"
                          onChange={e =>
                            setNewEncounter(p => ({
                              ...p, round_number: e.target.value
                            }))
                          }
                          placeholder="1, 2, 3..."
                        />
                      </div>
                    </div>

                    {!showCreateTeam ? (
                      <button
                        className="button link"
                        style={{ alignSelf: 'flex-start', fontSize: '0.75rem' }}
                        onClick={() => setShowCreateTeam(true)}
                      >
                        + Нет нужной команды? Создать
                      </button>
                    ) : (
                      <div className="sub-form-row">
                        <input
                          value={newTeamName}
                          className="input-field"
                          onChange={e => setNewTeamName(e.target.value)}
                          placeholder="Название команды"
                          onKeyDown={e => e.key === 'Enter' && handleCreateTeam()}
                        />
                        <button
                          className="button primary"
                          onClick={handleCreateTeam}
                          disabled={loading}
                        >
                          Создать
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => setShowCreateTeam(false)}
                        >
                          ✕
                        </button>
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: '0.75rem', paddingTop: '0.5rem' }}>
                      <button
                        className="button primary"
                        onClick={handleCreateEncounter}
                        disabled={loading}
                      >
                        {loading ? 'Создаём...' : 'Создать встречу'}
                      </button>
                      <button
                        className="button secondary"
                        onClick={() => setShowCreateEncounter(false)}
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </Card>
        )}

        {/* ШАГ 3: Загрузка файла */}
        {step === STEP.UPLOAD_FILE && selectedEncounter && (
          <Card
            title="Шаг 3 — Загрузите лог"
            subtitle={`${getTeamName(selectedEncounter.team1_id)} vs ${getTeamName(selectedEncounter.team2_id)}`}
            onBack={() => setStep(STEP.SELECT_ENCOUNTER)}
          >
            <FileDropZone file={file} onChange={setFile} />

            <div style={{ marginTop: '1rem' }}>
              <label className="form-label">
                Номер карты в серии (необязательно)
              </label>
              <input
                type="number"
                value={mapNumber}
                className="input-field"
                style={{ width: '8rem' }}
                onChange={e => setMapNumber(e.target.value)}
                placeholder="1, 2, 3..."
                min="1"
                max="7"
              />
            </div>

            <button
              className="button primary full-width"
              style={{ marginTop: '1.5rem' }}
              onClick={() => handleUpload()}
              disabled={!file || loading}
            >
              {loading ? (
                <span style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}>
                  <Spinner size="small" /> Загружаем...
                </span>
              ) : 'Загрузить лог'}
            </button>
          </Card>
        )}

        {/* ШАГ 4: Разрешение конфликтов */}
        {step === STEP.RESOLVE_CONFLICTS && (
          <Card
            title="Шаг 4 — Уточните игроков"
            subtitle="Несколько профилей с одинаковым ником"
          >
            <p style={{ fontSize: '0.875rem', color: '#a0aec0', marginBottom: '1rem' }}>
              Система нашла несколько игроков с одинаковым ником.
              Выберите правильный профиль для каждого.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {conflicts.map(conflict => (
                <div key={conflict.player_name} className="conflict-item">
                  <p className="player-name">{conflict.player_name}</p>
                  <div className="candidate-list">
                    {conflict.candidates.map(c => (
                      <label key={c.user_id} className="candidate-label">
                        <input
                          type="radio"
                          name={conflict.player_name}
                          value={c.user_id}
                          checked={
                            resolvedMappings[conflict.player_name] === String(c.user_id)
                          }
                          onChange={e =>
                            setResolvedMappings(p => ({
                              ...p,
                              [conflict.player_name]: e.target.value,
                            }))
                          }
                        />
                        <span className="username">{c.username}</span>
                        <span className="discord-id">Discord: {c.discord_id}</span>
                      </label>
                    ))}
                    <label className="candidate-label">
                      <input
                        type="radio"
                        name={conflict.player_name}
                        value="skip"
                        checked={resolvedMappings[conflict.player_name] === 'skip'}
                        onChange={() =>
                          setResolvedMappings(p => ({
                            ...p,
                            [conflict.player_name]: 'skip',
                          }))
                        }
                      />
                      <span className="username" style={{ color: '#6b7280' }}>
                        Не привязывать
                      </span>
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <button
              className="button primary full-width"
              style={{ marginTop: '1.5rem' }}
              onClick={handleResolveAndUpload}
              disabled={loading}
            >
              {loading ? 'Сохраняем...' : 'Подтвердить и сохранить'}
            </button>
          </Card>
        )}

        {/* ШАГ 5: Готово */}
        {step === STEP.DONE && result && (
          <Card title="✅ Лог успешно загружен!" className="done-card">
            <p style={{ fontSize: '0.875rem', color: '#a0aec0', marginBottom: '1rem' }}>
              Матч сохранён в базе данных.
            </p>
            <div className="button-group">
              <button
                className="button primary"
                onClick={() => navigate(`/matches/${result.match_id}`, {
                  state: { from: { url: window.location.pathname, label: 'UPLOAD MATCH' } }
                })}
              >
                Открыть матч
              </button>
              <button
                className="button secondary"
                onClick={() => {
                  setStep(STEP.UPLOAD_FILE)
                  setFile(null)
                  setMapNumber('')
                  setResult(null)
                  setError('')
                }}
              >
                Загрузить ещё
              </button>
              <button
                className="button link"
                onClick={() => navigate(`/encounters/${selectedEncounter?.id}`)}
              >
                К встрече →
              </button>
            </div>
          </Card>
        )}

      </div>
    </div>
  )
}

// ── Вспомогательные компоненты ────────────────────────────────────────────────

function StepBar({ current }) {
  const steps = [
    { id: 1, label: 'Турнир' },
    { id: 2, label: 'Встреча' },
    { id: 3, label: 'Файл' },
    { id: 4, label: 'Конфликты' },
    { id: 5, label: 'Готово' },
  ]

  const visibleSteps = steps.filter(s => s.id !== 4 || current >= 4)

  return (
    <div className="step-bar">
      {visibleSteps.map((s, i) => (
        <div key={s.id} style={{ display: 'flex', alignItems: 'center' }}>
          <div
            className={`step-item ${
              current === s.id
                ? 'step-item--active'
                : current > s.id
                ? 'step-item--done'
                : ''
            }`}
          >
            <span className="step-icon">
              {current > s.id ? '✓' : s.id}
            </span>
            <span>{s.label}</span>
          </div>
          {i < visibleSteps.length - 1 && (
            <div className="step-item-connector" />
          )}
        </div>
      ))}
    </div>
  )
}

function Card({ title, subtitle, children, onBack }) {
  return (
    <div className="upload-card">
      <div className="card-header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="subtitle">{subtitle}</p>}
        </div>
        {onBack && (
          <button className="back-button" onClick={onBack}>← назад</button>
        )}
      </div>
      {children}
    </div>
  )
}

function FileDropZone({ file, onChange }) {
  const [dragging, setDragging] = useState(false)

  const handleDrop = e => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f && f.name.endsWith('.txt')) onChange(f)
  }

  return (
    <div
      className={`file-drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".txt"
        onChange={e => onChange(e.target.files[0])}
      />
      {file ? (
        <div>
          <div className="icon">📄</div>
          <p className="text-main success">{file.name}</p>
          <p className="text-sub">
            {(file.size / 1024).toFixed(1)} KB · Нажмите чтобы заменить
          </p>
        </div>
      ) : (
        <div>
          <div className="icon">📂</div>
          <p className="text-main">Перетащите .txt файл сюда</p>
          <p className="text-sub">или нажмите для выбора</p>
        </div>
      )}
    </div>
  )
}

function Spinner({ size = 'large' }) {
  const s = size === 'small' ? '1rem' : '2rem'
  return (
    <div className="spinner">
      <svg
        className="spinner-svg"
        style={{ height: s, width: s }}
        viewBox="0 0 24 24"
      >
        <circle
          cx="12" cy="12" r="10"
          stroke="currentColor" strokeWidth="4"
          fill="none" opacity="0.25"
        />
        <path
          fill="currentColor" opacity="0.75"
          d="M4 12a8 8 0 018-8v8z"
        />
      </svg>
    </div>
  )
}