import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { tournamentsApi } from '../api/tournaments'
import { useAuth } from '../context/AuthContext'
import Header from '../components/layout/Header'
import RegisterModal from '../components/RegisterModal/RegisterModal'
import './TournamentDetail.css'
import BracketStage from '../components/tournament/bracket/BracketStage'

const COVER_MAP = [
  { keywords: ['mix #3', 'mix vol.3', 'mix vol 3'], cover: '/assets/images/tournaments/moonrise_mix_3.webp' },
  { keywords: ['mix #2', 'mix vol.2', 'mix vol 2'], cover: '/assets/images/tournaments/moonrise_mix_2.webp' },
  { keywords: ['mix #1', 'mix vol.1', 'mix vol 1'], cover: '/assets/images/tournaments/moonrise_mix_1.webp' },
  { keywords: ['mix'], cover: '/assets/images/tournaments/moonrise_mix_1.webp' },
  { keywords: ['valentine', '2x2', '2х2'], cover: '/assets/images/tournaments/valentines_cup.webp' },
  { keywords: ['draft'], cover: '/assets/images/tournaments/moonrise_draft.webp' },
  { keywords: ['lucio', 'wave'], cover: '/assets/images/tournaments/lucio_wave_clash.webp' },
  { keywords: ['nomercy', 'no mercy'], cover: '/assets/images/tournaments/nomercy_tournament.webp' },
]

function getCoverUrl(tournament) {
  if (tournament.cover_url) return tournament.cover_url
  const title = (tournament.title || '').toLowerCase()
  for (const entry of COVER_MAP) {
    if (entry.keywords.some(kw => title.includes(kw))) return entry.cover
  }
  return null
}

const MONTHS = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']
const MONTHS_SHORT = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

function formatDate(start, end) {
  if (!start) return '—'
  const s = new Date(start)
  const e = end ? new Date(end) : null
  if (!e || s.toDateString() === e.toDateString()) {
    return `${s.getDate()} ${MONTHS[s.getMonth()]}, ${s.getFullYear()}`
  }
  if (s.getMonth() === e.getMonth()) {
    return `${s.getDate()}-${e.getDate()} ${MONTHS[s.getMonth()]}, ${s.getFullYear()}`
  }
  return `${s.getDate()} ${MONTHS[s.getMonth()]} — ${e.getDate()} ${MONTHS[e.getMonth()]}, ${s.getFullYear()}`
}

function formatDateTime(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return `${d.getDate()} ${MONTHS_SHORT[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function getFormatLabel(format) {
  const map = { mix: 'Микс-турнир* без банов', draft: 'Драфт-турнир', start: 'Стартовый турнир', other: 'Особый формат' }
  return map[format] || format?.toUpperCase() || '—'
}

function getTabs(status) {
  if (status === 'completed' || status === 'cancelled') {
    return [
      { key: 'information', label: 'INFORMATION' },
      { key: 'schedule', label: 'SCHEDULE' },
      { key: 'participants', label: 'PARTICIPANTS' },
      { key: 'history', label: 'MATCH HISTORY' },
    ]
  }
  return [
    { key: 'information', label: 'INFORMATION' },
    { key: 'bracket', label: 'BRACKET' },
    { key: 'participants', label: 'PARTICIPANTS' },
    { key: 'history', label: 'MATCH HISTORY' },
  ]
}

const ROLE_FILTERS = ['all', 'tank', 'dps', 'sup', 'flex']

function ParticipantCard({ player, index }) {
  const checkedIn = player.status === 'checkedin'
  const allowed = player.is_allowed !== false
  return (
    <div className="td-p-card">
      <div className="td-p-card-header">
        <span className="td-p-card-num font-digits">{index}</span>
        {player.primary_role && (
          <div className="td-p-role-badge">
            <img src={`/assets/icons/icon-role-${player.primary_role}.svg`} alt="" className="td-p-badge-icon" />
            <span className="font-palui">{player.primary_role.toUpperCase()}</span>
          </div>
        )}
      </div>
      <div className="td-p-card-player">
        <div className="td-p-avatar">
          {player.avatar_url
            ? <img src={player.avatar_url} alt="" />
            : <span className="td-p-avatar-placeholder font-digits">{(player.display_name || '?')[0].toUpperCase()}</span>
          }
        </div>
        <div className="td-p-player-info">
          <span className="td-p-battletag font-ponter">{player.battle_tag || '—'}</span>
          <span className="td-p-nickname font-digits">{(player.display_name || '').toUpperCase()}</span>
        </div>
      </div>
      {player.bio && <p className="td-p-bio font-ponter">{player.bio}</p>}
      <div className="td-p-card-footer">
        <div className={`td-p-checkin ${checkedIn ? 'td-p-checkin-on' : ''}`}>
          <img src={checkedIn ? '/assets/icons/icon-check-in-on.svg' : '/assets/icons/icon-check-in.svg'} alt="" className="td-p-checkin-icon" />
          <span className="font-palui">CHECK-IN</span>
        </div>
        <div className={`td-p-allowed ${allowed ? 'td-p-allowed-yes' : 'td-p-allowed-no'}`}>
          {allowed && <img src="/assets/icons/icon-allowed.svg" alt="" className="td-p-allowed-icon" />}
          <span className="font-palui">{allowed ? 'ALLOWED' : 'NOT ALLOWED'}</span>
        </div>
      </div>
    </div>
  )
}

export default function TournamentDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  
  const [tournament, setTournament] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [message, setMessage] = useState(null)
  
  const [myStatus, setMyStatus] = useState(null)
  const [activeTab, setActiveTab] = useState('information')
  const [participantsTab, setParticipantsTab] = useState('players')
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  
  const [participants, setParticipants] = useState([])
  const [participantsLoading, setParticipantsLoading] = useState(false)
  
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false)
  const [userBattletags, setUserBattletags] = useState([])

  // Загрузка турнира
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await tournamentsApi.getById(id)
        setTournament(data)
      } catch {
        setMessage({ type: 'error', text: 'TOURNAMENT NOT FOUND' })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Загрузка статуса регистрации
  useEffect(() => {
    if (!user || !tournament) return
    const loadStatus = async () => {
      try {
        const data = await tournamentsApi.getMyStatus(id)
        setMyStatus(data)
      } catch (error) {
        console.error('Error loading status:', error)
      }
    }
    loadStatus()
  }, [user, tournament, id])

  // Загрузка BattleTag пользователя (только если авторизован)
  useEffect(() => {
    if (!user) return
    const loadBattletags = async () => {
      try {
        const token = localStorage.getItem('moonrise_token')
        if (!token) return
        const response = await fetch('/api/users/me/battletags', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          const data = await response.json()
          setUserBattletags(data.battletags || [])
        }
      } catch (error) {
        console.error('Error loading battletags:', error)
      }
    }
    loadBattletags()
  }, [user])

  // Загрузка участников турнира
   useEffect(() => {
    if (activeTab !== 'participants') return;
    setParticipantsLoading(true);
    
    // ✅ ИСПОЛЬЗУЕМ tournamentsApi ВМЕСТО СЫРОГО fetch!
    tournamentsApi.getParticipants(id)
      .then(data => {
        setParticipants(Array.isArray(data) ? data : data.participants || []);
      })
      .catch(err => {
        console.error("Ошибка загрузки участников:", err);
        setParticipants([]);
      })
      .finally(() => {
        setParticipantsLoading(false);
      });
  }, [activeTab, id]);

  const handleAction = async () => {
    if (!user) {
      window.location.href = '/api/auth/discord'
      return
    }

    // Если регистрация открыта и статус не "одобрено"/"на рассмотрении", открываем модалку
    if (tournament.status === 'registration') {
      if (!myStatus?.registered || myStatus?.status === 'rejected') {
        setIsRegisterModalOpen(true)
        return
      }
    }

    // Обработка Check-In
    if (myStatus?.status === 'registered' && tournament.status === 'checkin') {
      setActionLoading(true)
      setMessage(null)
      try {
        await tournamentsApi.checkin(id)
        setMessage({ type: 'success', text: 'CHECK-IN CONFIRMED!' })
        const updatedStatus = await tournamentsApi.getMyStatus(id)
        setMyStatus(updatedStatus)
      } catch (err) {
        const detail = err?.response?.data?.detail || 'SOMETHING WENT WRONG'
        setMessage({ type: 'error', text: detail.toUpperCase() })
      } finally {
        setActionLoading(false)
      }
    }
  }

  // Отрисовка главной кнопки действий
  const renderActionButton = () => {
    const { status } = tournament

    if (status === 'completed' || status === 'cancelled')
      return <button className="td-btn td-btn-completed font-palui" disabled>TOURNAMENT COMPLETED</button>

    if (status === 'ongoing')
      return <button className="td-btn td-btn-live font-palui" disabled>🔴 LIVE</button>

    if (!user)
      return <button className="td-btn td-btn-register font-palui" onClick={handleAction}>REGISTRATION</button>

    // Статусы пользователя
    if (myStatus?.status === 'checkedin')
      return <button className="td-btn td-btn-disabled font-palui" disabled>✓ CHECK-IN CONFIRMED</button>

    if (myStatus?.status === 'registered' && myStatus?.is_allowed) {
      if (status === 'checkin') {
        return <button className="td-btn td-btn-register font-palui" onClick={handleAction} disabled={actionLoading}>
          {actionLoading ? '...' : '✓ CHECK-IN NOW'}
        </button>
      }
      return <button className="td-btn td-btn-disabled font-palui" disabled>✓ ОДОБРЕНЫ</button>
    }

    if (myStatus?.status === 'pending')
      return <button className="td-btn td-btn-disabled font-palui" disabled>⏳ ОЖИДАНИЕ ПОДТВЕРЖДЕНИЯ</button>

    if (myStatus?.status === 'rejected') {
      if (status === 'registration') {
        return <button className="td-btn td-btn-register font-palui" onClick={handleAction}>ПЕРЕПОДАТЬ ЗАЯВКУ</button>
      }
      return <button className="td-btn td-btn-disabled font-palui" disabled>ЗАЯВКА ОТКЛОНЕНА</button>
    }

    if (status === 'registration')
      return <button className="td-btn td-btn-register font-palui" onClick={handleAction}>REGISTRATION</button>

    return <button className="td-btn td-btn-disabled font-palui" disabled>REGISTRATION NOT OPEN</button>
  }

  if (loading) return (
    <div className="td-page">
      <Header />
      <div className="td-loading">
        <div className="td-spinner"/>
        <span className="font-palui">LOADING...</span>
      </div>
    </div>
  )

  if (!tournament) return (
    <div className="td-page">
      <Header />
      <div className="td-loading">
        <p className="font-palui">NOT FOUND</p>
        <Link to="/tournaments" className="td-back font-palui">‹ BACK TO TOURNAMENTS</Link>
      </div>
    </div>
  )

  const tabs = getTabs(tournament.status)
  const cover = getCoverUrl(tournament)

  const filteredParticipants = participants.filter(p => {
    const matchSearch = !searchQuery ||
      (p.battle_tag || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.display_name || '').toLowerCase().includes(searchQuery.toLowerCase())
    const matchRole = roleFilter === 'all' || p.primary_role === roleFilter || p.secondary_role === roleFilter
    return matchSearch && matchRole
  })

  return (
    <div className="td-page">
      <Header />
      <main className="td-main">
        <div className="td-container">
          
          <nav className="td-breadcrumb font-digits">
            <Link to="/tournaments">TOURNAMENTS</Link>
            <span className="td-bc-sep"> › </span>
            <span className="td-bc-current">
              {tournament.title.length > 40
                ? tournament.title.toUpperCase().slice(0, 40) + '...'
                : tournament.title.toUpperCase()}
            </span>
          </nav>

          <div className="td-grid">
            <aside className="td-sidebar">
              <div className="td-poster-wrap">
                <img src="/assets/icons/corner-bracket.svg" alt="" className="td-corner td-corner-tl" />
                <img src="/assets/icons/corner-bracket.svg" alt="" className="td-corner td-corner-tr" />
                <img src="/assets/icons/corner-bracket.svg" alt="" className="td-corner td-corner-bl" />
                <img src="/assets/icons/corner-bracket.svg" alt="" className="td-corner td-corner-br" />
                {cover
                  ? <img src={cover} alt={tournament.title} className="td-poster-img" />
                  : <div className="td-poster-placeholder"><span className="font-palui">NO IMAGE</span></div>
                }
              </div>

              <div className="td-sidebar-title-row">
                <img src="/assets/icons/mix_icon.svg" alt="" className="td-title-icon" />
                <h1 className="td-sidebar-name font-palui">
                  {tournament.title.toUpperCase().includes('#') ? (
                    <>
                      <span>{tournament.title.toUpperCase().split('#')[0]}</span>
                      <span className="font-digits" style={{ marginLeft: '4px', letterSpacing: '0.05em' }}>
                        #{tournament.title.toUpperCase().split('#')[1]}
                      </span>
                    </>
                  ) : (
                    <span>{tournament.title.toUpperCase()}</span>
                  )}
                </h1>
              </div>

              <div className="td-sidebar-meta">
                <div className="td-meta-item">
                  <img src="/assets/icons/calend.svg" alt="" className="td-meta-icon" />
                  <span className="font-ponter">{formatDate(tournament.start_date, tournament.end_date)}</span>
                </div>
                <div className="td-meta-item">
                  <img src="/assets/icons/people.svg" alt="" className="td-meta-icon" />
                  <span className="font-ponter">{tournament.max_participants || 100}</span>
                </div>
                <div className="td-meta-item">
                  <img src="/assets/icons/icon-teams.svg" alt="" className="td-meta-icon" />
                  <span className="font-ponter">12 TEAMS</span>
                </div>
              </div>

              {/* Блок с кнопками: Регистрация, Регламент, Админ-панель */}
              <div className="td-actions" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', margin: '1rem 0' }}>
                {renderActionButton()}
                
                <button className="td-btn td-btn-rules font-palui">РЕГЛАМЕНТ</button>
                
                {user?.role === 'admin' && (
                  <Link
                    to={`/admin/tournaments/${id}/applications`}
                    className="td-btn font-palui"
                    style={{ backgroundColor: '#13c8b0', color: 'white', flex: '1 1 100%', textAlign: 'center' }}
                  >
                    АДМИН-ПАНЕЛЬ
                  </Link>
                )}
              </div>

              {message && (
                <div className={`td-message td-message-${message.type} font-ponter`}>
                  {message.text}
                </div>
              )}
            </aside>

            <div className="td-content">
              <div className="td-tabs">
                {tabs.map(tab => (
                  <button
                    key={tab.key}
                    className={`td-tab font-digits ${activeTab === tab.key ? 'td-tab--active' : ''}`}
                    onClick={() => setActiveTab(tab.key)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="td-tab-body">
                {activeTab === 'information' && (
                  <div className="td-info">
                    <div className="td-section">
                      <h2 className="td-section-title font-palui">ОБЩАЯ ИНФОРМАЦИЯ</h2>
                      <div className="td-section-body">
                        <p className="font-montserrat">
                          <span className="td-label">Платформа:</span> ПК
                        </p>
                        <p className="font-montserrat">
                          <span className="td-label">Формат:</span> {getFormatLabel(tournament.format)}
                        </p>
                        <p className="td-desc font-montserrat">
                          *В формате микс-турнира команды формируются организаторами с помощью инструментов для баланса команд. Основной принцип формирования команд — баланс среднего рейтинга между всеми командами.
                        </p>
                      </div>
                    </div>

                    <div className="td-section">
                      <h2 className="td-section-title font-palui">ДАТЫ ПРОВЕДЕНИЯ:</h2>
                      <div className="td-section-body">
                        <p className="font-montserrat">
                          <span className="td-label">День 1:</span> групповой этап - 28 марта, 16:00 по МСК
                        </p>
                        <p className="font-montserrat">
                          <span className="td-label">День 2:</span> плей-офф - 29 марта, 16:00 по МСК
                        </p>
                        <p className="font-montserrat">
                          <span className="td-label">Регистрация:</span> с 23 по 26 марта 23:59 по МСК
                        </p>
                        <p className="font-montserrat">
                          <span className="td-label">Чек-ин:</span> 27 марта, с 16:00 по 19:00 по МСК
                        </p>
                        <p className="td-bold-line font-montserrat">
                          Список команд будет опубликован 27 марта.
                        </p>
                      </div>
                    </div>

                    <div className="td-section">
                      <h2 className="td-section-title font-palui">ТРЕБОВАНИЯ ДЛЯ УЧАСТИЯ:</h2>
                      <div className="td-section-body">
                        <p className="font-montserrat">К участию допускаются игроки, соответствующие следующим условиям:</p>
                        <ul className="td-req-list">
                          <li className="font-montserrat">
                            <span className="td-label">Минимальный рейтинг:</span> Золото 3 (на основной и дополнительной роли)
                          </li>
                          <li className="font-montserrat">
                            <span className="td-label">Откалиброванный рейтинг</span> на обеих ролях в текущем сезоне
                          </li>
                          <li className="font-montserrat">
                            Минимум <span className="td-label">100 часов</span> в игре на аккаунте
                          </li>
                          <li className="font-montserrat">
                            <span className="td-label">Открытый профиль</span> (в игровых настройках сделать аккаунт открытым)
                          </li>
                          <li className="font-montserrat">
                            Добавить в друзья аккаунт организаторов турнира - <span className="td-highlight">Steve#24919</span>
                          </li>
                          <li className="font-montserrat">
                            <span className="td-label">Для стримеров:</span> установить задержку минимум 40 секунд
                          </li>
                          <li className="font-montserrat">
                            Вся коммуникация команды во время турнира должна проходить <span className="td-highlight">в специально отведенном канале</span> на сервере MoonRise
                          </li>
                        </ul>
                        <p className="td-note font-montserrat">
                          Принимая участие в турнире MoonRise Mix участники автоматически соглашаются с регламентом его проведения.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {activeTab === 'bracket' && (
                  <div className="td-bracket-wrapper" style={{ paddingTop: '10px' }}>
                    <BracketStage />
                    </div>
                  )}

                {activeTab === 'schedule' && (
                  <div className="td-placeholder">
                    <span className="font-palui">SCHEDULE — COMING SOON</span>
                  </div>
                )}

                {activeTab === 'participants' && (
                  <div className="td-participants">
                    <div className="td-p-subtabs">
                      <button
                        className={`td-p-subtab font-digits ${participantsTab === 'players' ? 'td-p-subtab--active' : ''}`}
                        onClick={() => setParticipantsTab('players')}
                      >
                        УЧАСТНИКИ
                      </button>
                      <button
                        className={`td-p-subtab font-digits ${participantsTab === 'teams' ? 'td-p-subtab--active' : ''}`}
                        onClick={() => setParticipantsTab('teams')}
                      >
                        КОМАНДЫ
                      </button>
                    </div>

                    <div className="td-p-controls">
                      <div className="td-p-search-wrap">
                        <img src="/assets/icons/lupa.svg" alt="" className="td-p-search-icon" />
                        <input
                          className="td-p-search font-ponter"
                          placeholder="ПОИСК УЧАСТНИКА..."
                          value={searchQuery}
                          onChange={e => setSearchQuery(e.target.value)}
                        />
                      </div>
                      <div className="td-p-roles">
                        {ROLE_FILTERS.map(role => (
                          <button
                            key={role}
                            className={`td-p-role-btn font-palui ${roleFilter === role ? 'td-p-role-btn--active' : ''}`}
                            onClick={() => setRoleFilter(role)}
                          >
                            {role !== 'all' && (
                              <img src={`/assets/icons/icon-role-${role}.svg`} alt="" className="td-p-role-icon" />
                            )}
                            {role.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </div>

                    {participantsTab === 'players' && (
                      participantsLoading
                        ? <div className="td-loading-small"><div className="td-spinner"/></div>
                        : filteredParticipants.length === 0
                          ? <p className="td-empty font-ponter">Нет участников</p>
                          : (
                            <div className="td-p-grid">
                              {filteredParticipants.map((p, i) => (
                                <ParticipantCard key={p.id || i} player={p} index={i + 1} />
                              ))}
                            </div>
                          )
                    )}

                    {participantsTab === 'teams' && (
                      <div className="td-placeholder">
                        <span className="font-palui">КОМАНДЫ БУДУТ СФОРМИРОВАНЫ ПОЗЖЕ</span>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'history' && (
                  <div className="td-placeholder">
                    <span className="font-palui">MATCH HISTORY — COMING SOON</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <Link to="/tournaments" className="td-back font-palui">‹ BACK TO TOURNAMENTS</Link>

          {/* Модальное окно регистрации */}
          {user && tournament && (
            <RegisterModal
              tournament={tournament}
              isOpen={isRegisterModalOpen}
              onClose={() => setIsRegisterModalOpen(false)}
              onSuccess={async () => {
                try {
                  const data = await tournamentsApi.getMyStatus(id)
                  setMyStatus(data)
                  const updatedTournament = await tournamentsApi.getById(id)
                  setTournament(updatedTournament)
                } catch (error) {
                  console.error('Error updating status:', error)
                }
              }}
              userBattletags={userBattletags}
            />
          )}
        </div>
      </main>
    </div>
  )
}