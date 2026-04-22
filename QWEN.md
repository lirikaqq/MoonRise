## Qwen Added Memories
- Весь проект MoonRise: ВСЕГДА отвечать на русском языке, никогда не использовать английский в ответах. Это касается всех файлов, кода, комментариев, документации и коммуникации по проекту.
- ANALYSIS OF anak-tournaments (github.com/CraazzzyyFoxx/anak-tournaments) — saved for reference in MoonRise project:

ARCHITECTURE:
- Two backend services: app-service (main API) + parser-service (log parsing)
- Frontend: Next.js + TypeScript + Shadcn/UI
- Infra: Kong (API gateway), RabbitMQ (queues), S3 (log storage), PostgreSQL, Redis (caching)

DB MODELS (match.py):
- Match: home_team_id, away_team_id, home_score, away_score, time, log_name, encounter_id, map_id
- MatchStatistics (EAV model): match_id, round, team_id, user_id, hero_id, name (LogStatsName enum), value (float)
- MatchKillFeed: match_id, time, round, fight, ability (AbilityEvent), killer_id/hero_id/team_id, victim_id/hero_id/team_id, damage, is_critical_hit, is_environmental
- MatchEvent (match_assists): match_id, time, round, team_id, user_id, hero_id, name (OffensiveAssist, DefensiveAssist, UltimateCharged/Start/End, HeroSwap, MercyRez, EchoDuplicateStart/End)

ENUMS (enums.py):
- LogEventType: MatchStart, MatchEnd, PlayerJoined, RoundStart, RoundEnd, Kill, OffensiveAssist, DefensiveAssist, UltimateCharged/Start/End, HeroSwap, MercyRez, EchoDuplicateStart/End, PlayerStat
- LogStatsName (base): Eliminations, FinalBlows, Deaths, HeroDamageDealt, HealingDealt, DamageBlocked, SoloKills, ObjectiveKills
- LogStatsName (derived): KD, KDA, DamageDelta, Performance, PerformancePoints, FBE, DamageFB, Assists
- MatchEvent: OffensiveAssist, DefensiveAssist, UltimateCharged/Start/End, HeroSwap, MercyRez, EchoDuplicateStart/End
- AbilityEvent: PrimaryFire, SecondaryFire, Ability1, Ability2, Ultimate, Melee, Crouch

PARSER-SERVICE FLOW (flows.py — MatchLogProcessor):
1. _load_and_format_data: CSV parsing, round_number via cumulative RoundStart count
2. validate: Check MatchEnd exists, delete from S3 if incomplete
3. get_map: Extract gamemode, map_name from MatchStart
4. process_teams: Match team names from MatchStart, players from PlayerJoined, DB lookup via UserBattleTag (case-insensitive), team match by 3+ roster players, handle substitutions
5. start: Find/create/update Match by encounter+map, delete old stats/kills/events, recreate
6. process_kills: All Kill events sorted by time → MatchKillFeed. Fight ID: 15s gap = new fight
7. process_events: OffensiveAssist, DefensiveAssist, UltimateCharged/Start/End, HeroSwap, EchoDuplicate, MercyRez (with target)
8. create_stats: PlayerStat events (cumulative) → diff() for discrete values. round>0 = per-round per-hero + per-round aggregate. round=0 = full-match per-hero + full-match aggregate. Derived metrics: KD=elim/max(deaths,1), KDA=(elim+assists)/max(deaths,1), DamageDelta=hero_dmg-dmg_taken, PerformancePoints=elim*500+fb*250+assists*50+hero_dmg+healing*1-deaths*750+blocked*0.1, Performance=rank by PerformancePoints within round

API ENDPOINTS:
- app-service: GET /matches, GET /matches/{id}, GET /encounters, GET /encounters/{id}, GET /statistics/champion, GET /statistics/winrate, GET /statistics/won-maps
- parser-service: POST /logs/, GET /logs/{tournament_id}, POST /logs/{tournament_id}, POST /logs/{tournament_id}/upload, POST /logs/{tournament_id}/discord, POST /logs/{tournament_id}/{filename}
- Async processing via RabbitMQ: PROCESS_MATCH_LOG_QUEUE, PROCESS_TOURNAMENT_LOGS_QUEUE

FRONTEND (Next.js App Router):
- /encounters — list, /encounters/[id] — detail with EncounterMatch dialog (tabs: All Match + Round N)
- /matches — paginated table, /matches/[id] — detail page
- MatchTeamTable columns: Player, Role, Heroes, PRS (Performance Badge), FB, E, D, A, K/D, KA/D, SK, OK, Hero Damage, Dmg/FB, Healing, Blocked, Delta Damage, Ult Used/Earned
- MatchStatsChart: Recharts BarChart for Kills/Assists per player
- NO Kill Feed UI component (table exists in DB but not displayed)

KEY DIFFERENCES FROM MOONRISE:
- EAV stats model (flexible) vs flat columns
- Derived metrics (KD, KDA, PerformancePoints, Performance rank)
- Fight detection (15s gap)
- Discrete per-round stats via diff()
- Rich MatchTeamTable (15+ columns)
- Bar chart visualization
- S3 + RabbitMQ async processing

LOCATION: c:\Users\Артём\OneDrive\Рабочий стол\MoonRise\anak-tournaments-master
- ANAK BALANCER SERVICE — полный разбор:

ARCHITECTURE:
- Два процесса: Balancer API (FastAPI, порт 8003) + Balancer Worker (FastStream/RabbitMQ)
- Стейт в Redis: balancer:job:{id}:{meta|payload|result|events|event_seq}
- Redis TTL для авто-очистки completed jobs

API ENDPOINTS:
- POST /api/balancer/jobs — multipart (file + config) → {job_id, status_url, result_url, stream_url}
- GET /api/balancer/jobs/{job_id} — статус: queued/running/succeeded/failed + прогресс
- GET /api/balancer/jobs/{job_id}/result — результат (только succeeded)
- GET /api/balancer/jobs/{job_id}/stream — SSE-стрим прогресса в реальном времени
- GET /api/balancer/config — дефолты + пресеты для фронтенда

INPUT FORMAT (JSON file):
{ "format": "xv-1", "players": { "uuid": { "identity": {"name": "Player#1234"}, "stats": {"classes": {"Damage": {"rank":1700,"isActive":true,"priority":1}}}}}}

GENETIC ALGORITHM (service.py):
- Классы: Player (uuid, name, ratings{}, discomfort_map{}, preferences[]), Team (roster{role: [players]}, cached stats)
- Параметры: POPULATION_SIZE=200, GENERATIONS=750, ELITISM_RATE=0.2, MUTATION_RATE=0.4, MUTATION_STRENGTH=3
- Функция стоимости: cost = inter_std*3.0 + avg_discomfort*0.25 + avg_intra_std*0.8 + global_max_pain*1.0
- Мутации: 70% межкомандный swap роли, 30% внутрикомандный swap ролей
- Ранний стоп при cost <= 0.1

DISCOMFORT SYSTEM:
- Роль #1 в предпочтениях → discomfort = 0
- Роль #2 → 100, #3 → 200
- Не в предпочтениях но есть рейтинг → 1000
- Нет рейтинга → 5000

OUTPUT FORMAT:
{ "teams": [{ "id":7, "name":"Captain#1234", "avgMMR":1000.0, "variance":529.15, "totalDiscomfort":0, "maxDiscomfort":0, "roster":{ "Damage":[{uuid,name,rating,discomfort,isCaptain,preferences[],allRatings{}}], "Support":[...] }}], "statistics":{ "averageMMR":1000.4, "mmrStdDev":2.15, "totalTeams":12, "playersPerTeam":5 }}

CONFIG PRESETS:
- Default: POPULATION=200, GENERATIONS=750, MMR_WEIGHT=3.0
- Competitive: POPULATION=300, GENERATIONS=1000, MMR_WEIGHT=5.0, USE_CAPTAINS=true
- Quick: POPULATION=50, GENERATIONS=200, USE_CAPTAINS=false

JOB STORE (Redis-backed):
- create_job(), get_job_meta(), get_job_payload(), get_job_result()
- append_event() — добавляет событие в список + обновляет meta
- mark_running(), mark_succeeded(), mark_failed()
- get_events_since() — для SSE-стриминга
- Auto-TTL refresh при каждом update

SSE STREAMING:
- GET /jobs/{id}/stream с Last-Event-ID header для resume
- Формат: "id: {event_id}\ndata: {json}\n\n"
- Heartbeat каждые 1 сек
- Авто-стоп при terminal status + no new events

KEY INSIGHTS:
- Генетический алгоритм — готовый модуль, можно перенести в MoonRise
- Redis job store — асинхронный баланс без блокировки UI
- SSE — прогресс в реальном времени
- Discomfort system — учёт предпочтений ролей игроков
- Captains — топ-N по max_rating распределяются по разным командам
- Copy-on-write мутации — оптимизация: копируется только затронутая команда

LOCATION: c:\Users\Артём\OneDrive\Рабочий стол\MoonRise\anak-tournaments-master\backend\balancer-service
- MOONRISE PROJECT — ПОЛНЫЙ ДАМП РЕАЛИЗАЦИИ (состояние на 2026-04-09)
- MOONRISE PROJECT — ОБНОВЛЕНИЕ 2026-04-09 (Многоэтапная система турниров v4.0)
- MOONRISE PROJECT — UPDATE 2026-04-09 (PlayerProfile v7.0 + Stages v4.0)
- РЕФЕРЕНС МАКЕТА PLAYER PROFILE: Kleiner — профиль на странице турнира MoonRise Mix Vol.3.

Визуал:
- Левая колонка: PlayerCard (Kleiner, avatar 45x45, battletag kleiner#21367 +8, twitch kleiner), AchievementsCard (6 иконок), DivisionsCard (Tank 6, DPS 14, Sup 14)
- Правая колонка:
  - Вкладки: OVERVIEW (active, #A7F2A2 underline, оторван на 5px от основной линии), TOURNAMENTS, ACHIEVEMENTS
  - Основная линия под вкладками: #13AD91, 2px
  - FilterRow: select "MOONRISE MIX VOL. 3", 3.6. PLAYTIME, 10 MAPS, 8 WIN / 2 LOSE (WIN=#13AD91, LOSE=#A7F2A2)
  - StatsTopRow: 12 PLACE, TANK (с иконкой 6), MVP SCORE 24.28 (20 FROM 100), SVP SCORE 3.44 (28 FROM 220)
  - StatsBottomRow: WINRATE 100% (5 FROM 12), KDA RATIO 4.57 (33 FROM 100), ELIMS 24.28 (20 FROM 100), DEATHS 6.89 (26 FROM 100)
  - TopHeroesCard: MERCY (10H 9M), GENJI (5H 58M), D.VA (48M) — каждый с ELIMS/DAMAGE/DEATHS/HEALING карточками + GLOBAL AVG/ID

Ключевая особенность вкладок:
- OVERVIEW активна: background rgba(167,242,162,0.08), текст #A7F2A2
- Основная линия border-bottom: 2px #13AD91
- Подчёркивание активной вкладки через ::after: bottom:-5px (оторвано от линии), height:4px, background #A7F2A2

Расположение изображений: c:\Users\Артём\.qwen\tmp\clipboard\clipboard-1775772217667-d6084ef9-5a3d-432f-a9ae-37f87b951612.png (вкладки крупно), clipboard-1775772217743-16a33ab3-6690-4084-8f40-5535233e4ac3.png (полная страница)
- ОШИБОЧНАЯ РЕАЛИЗАЦИЯ — анимация переключения табов в PlayerProfile (апрель 2026):
State-машина (activeTab/targetTab/tabPhase) + .tabPanel с position:absolute + .band-right--top position:relative — СЛОМАЛО corner-line (красные диагональные линии) на карточках статистики в правой полосе. Причина: position:relative на .band-right--top изменил контекст абсолютного позиционирования для всех corner-line внутри.
ПРАВИЛЬНЫЙ ПОДХОД: делать анимацию табов БЕЗ абсолютного позиционирования на контейнере контента. Использовать opacity/transition на условно-рендеримых элементах, сохраняя нормальный поток документа.
- ДИЗАЙН-СПЕЦИФИКАЦИЯ PLAYER PROFILE (Overview) — pixel-perfect от дизайнера:

GLOBAL LAYOUT: Band1=255px, Band2=160px, Band3=250px, row-gap=20px, left-col=450px, right-col=1120px, page-padding=148px

PLAYERCARD (450×255, padding=30, skew=30px, stroke=0): accent-line 5×230px left:0, avatar 100×100 top:30 left:30 border:1px #A7F2A2 radius:10, name 40px Arial Black top:30 left:150, battletag 130×25 padding 7/15/7/15 border 1px #A7F2A2 gap:8 badge+8, nick→battletag:10, twitch icon 17×20 gap:10 text 17px Arial, battletag→twitch:12, twitch→divider:21, divider 1px #A7F2A2 length:390 left:30 right:30, divider→stats:109, stats font-size 35/17 Ponter, vertical-gap digit→label:35, text-align:center, horizontal-gap between 3 blocks:35

TABS: total-height:70, tab-height:45, padding:12/41/18/41, gap:0, cyan-line:1px, active-underline:5px #A7F2A2, active-bg:#23423F, active-padding-left-right:74, text→underline:13, active/inactive font-weight-diff:0

FILTERROW (h:40, margin-from-tabs:25): dropdown 325×40 padding 11/172/14/22 text→arrow-gap:129 arrow:25×15 radius:5, dropdown→playtime-icon:50, playtime-icon→text:15, font:18px ST-SimpleSquare, playtime→maps-icon:50, maps-icon→text:15, winlose w:300 h:40 padding:13/34/13/34 gap:70 bg-win:#13AD91 bg-lose:#A7F2A2 radius:40 border:1px #111B25, diagonal-divider:1px 45deg

TOP ROW CARDS (h:90, padding:20/20/20/35, skew:20px, stroke:0): accent-line 5×75px left:0 #13AD91, gap:20, PLACE:36px+17px Ponter, TANK icon+text 24px ST, MVP/SVP: label 17px Ponter, value 30px ST, sub 11px Ponter

BOTTOM ROW CARDS (h:160, padding:30, skew:30px, stroke:1): accent-line 10×100px left:30 gradient, gap:20, label 14px Ponter, value 42px ST, sub 13px Ponter

ACHIEVEMENTSCARD (450×160, padding:30, skew:30px, border:1px #13AD91): title→line:20, line:2px #13AD91, line→slots:35, slots 55×55 gap:10 border:1px #13AD91 padding:15, icon 32×32

DIVISIONSCARD (450×250, padding:30, skew:30px, border:1px #13AD91): title→line:20, line:2px #13AD91, blocks 130×145 gap:0

TOPHEROESCARD (1120×250, padding:30, skew:30px, stroke:1): title top:30, title→subtitle-gap:111, title 21px ST, subtitle 12px #A7F2A2, line below header, heroes 3-col gap:30, avatar 100×100 border:1px #A7F2A2 radius:10, avatar→name:30, name 13px Ponter #13AD91, name→playtime:6, playtime 13px #A7F2A2, stats-cards 105×65 padding:10 skew:10px border:1px #13AD91, avatar-right-edge→elims:10, v-gap:10, h-gap label→value:5, label 12px ST, value 15px Ponter #A7F2A2, global 10px Ponter #A7F2A2, value→global:5
- PLAYER PROFILE — ОБНОВЛЕНИЯ (2026-04-13):

CSS СТРУКТУРА PLAYERCARD:
- Новый layout: player-card__header (avatar-wrapper + profile-info) → hr divider → statsrow (3 stat-item)
- player-card__usertag: display flex, align-items center (иконка Twitch + текст)
- player-card__statsrow: flex, justify-content space-between, 3× flex-1
- Убраны ::before/::after (accent обводка с inset) — оставлен простой clip-path
- Clip-path: оба угла скошены (левый верхний + правый нижний) через var(--skew-*)

ОБВОДКА КАРТОЧЕК — УБРАНА ВЕЗДЕ:
- Все карточки (stat-card-small, stat-card-large, top-heroes-card, achievements-card, divisions-card, player-card) — просто clip-path + background: var(--block-bg)
- Нет ::before (accent border) и ::after (inset:1px bg)

ФОН СТРАНИЦЫ:
- body: linear-gradient(180deg, #1D353E 0%, #111B25 100%), background-attachment: fixed
- Убраны конфликтующие фоны: pages/PlayerProfilePage.css .player-profile-page (transparent), pages/PlayerProfile.css .profile-page (transparent)
- pages/PlayerProfile.css .profile-page был с radial-gradient — заменён на transparent

ШРИФТЫ — ЗАМЕНА --font-st НА "Digits":
- ProfileTabs.css, FilterRow.css, StatsBottomRow.css, StatsTopRow.css, TopHeroesCard.css, DivisionsCard.css, AchievementsCard.css, PlayerProfile.css, PlayerProfile.jsx — все font-family: var(--font-st) → font-family: "Digits", sans-serif

PROFILE TABS:
- Убран font-weight: 700 из .profile-tab
- Добавлена hr-линия под табами: profile-tabs__line (border-top: 1px solid var(--accent), width: 1121px)

PLACE И TANK КАРТОЧКИ (StatsTopRow):
- PLACE: горизонтальный layout (число #13AD91 + слово #A7F2A2 в одну строку)
- TANK: SVG щит (Material Shield) вместо PNG, цвет var(--accent), горизонтально с текстом
- Убраны font-weight: 700 и letter-spacing

DIVISIONS CARD:
- Текстовые префиксы (♥, !!!, +) заменены на SVG-иконки ролей: icon-role-tank.svg, icon-role-dps.svg, icon-role-sup.svg

КОНФЛИКТ PLAYER-CARD ИСПРАВЛЕН:
- DraftPage.css имел глобальный .player-card с border: 1px solid #3a5160 + border-radius: 8px
- Решение: селектор .draft-pool-container .player-card (специфичный для драфта)
- PLAYER PROFILE CSS — КЛЮЧЕВЫЕ РЕШЕНИЯ (сессия 2026-04-10):

1. StatsTopRow.css — акцентная линия: width:5px, height:100%, background: var(--accent) СПЛОШНОЙ, НЕ градиент
2. StatsTopRow.css — фон карточки: background: var(--block-bg) БЕЗ градиентов
3. StatsTopRow.css — MVP/SVP карточки: горизонтальный layout (лейбл слева, значение справа)
4. FilterRow.css — WIN/LOSE пилюля: clip-path: polygon() на обоих блоках для диагонального среза, между ними 1px просвет виден фон родителя
5. ProfileTabs.jsx — сдвиг табов: style={{ position: 'relative', left: '-3px', top: '17px' }}
6. PlayerProfile.css — .profile-band-1: align-items: end (карточка прижата к низу)
7. AchievementsCard — все 6 ачивок через <img src="...">, locked: background: transparent, border: rgba(19,173,145,0.3)
8. FilterRow — все иконки через <img> вместо inline SVG (dropdown, playtime, maps)
9. StatsBottomRow.css — акцентная линия: градиент #13AD91 → #A7F2A2, width:10px height:100px, top:30px left:30px, padding-left:65px у контента
10. StatsTopRow.jsx — ROLE иконка: <img src={ROLE_ICONS[role]}> динамически подставляет tank/dps/sup
11. PlayerCard.jsx — Twitch иконка: <img src="/assets/icons/mini_twitch.svg"> вместо inline SVG
12. PlayerProfile.css :root — только 3 цвета (--accent:#13AD91, --accent-light:#A7F2A2, --block-bg:#111B25), остальное не трогать
- MOONRISE PROJECT — PLAYER PROFILE CLAIM SYSTEM (2026-04-14)

STATUS: Frontend design полностью завершён (PlayerProfile + все компоненты: PlayerCard, FilterRow, StatsTopRow, StatsBottomRow, TopHeroesCard, AchievementsCard, DivisionsCard). Анимация Flip Card на стат-карточках активна. Демо-данные в PlayerProfile.jsx (DEMO_PLAYER, DEMO_STATS).

ПРОБЛЕМА: Ghost-профили создаются автоматически из логов без Discord. Любой может теоретически захватить чужой профиль. Нужно защитить профили от "захвата".

РЕШЕНИЕ: Profile Claim System с админ-апрувом (без OAuth).
Battle.net OAuth НЕВОЗМОЖЕН для РФ аккаунтов (Dev Portal заблокирован).
Twitch OAuth возможен, но не нужен для OW2 статистики.

МЕХАНИЗМ CLAIM:
1. Игрок регистрируется через Discord → вводит BattleTag вручную (например Kleiner#21367)
2. Система ищет ghost-профили в БД с точным совпадением BattleTag (case-insensitive)
3. Кнопка "Это мой профиль — заявить права" появляется на странице ghost-профиля
4. Создаётся ProfileClaimRequest (status=pending)
5. Админ видит заявку в админке → Approve / Reject
6. При Approve: merge данных из ghost в основной аккаунт, ghost блокируется
7. Только владелец Discord-аккаунта может редактировать профиль

НОВАЯ МОДЕЛЬ БД — ProfileClaimRequest:
- id (Integer PK)
- user_id (FK → users.id) — Discord-аккаунт заявителя
- ghost_user_id (FK → users.id) — Ghost-профиль который забирают
- battletag_match (String) — BattleTag который совпал
- status (Enum: pending/approved/rejected)
- admin_note (String) — комментарий админа при отклонении
- created_at (DateTime)
- resolved_at (DateTime)

РАСШИРЕНИЕ МОДЕЛИ User:
- claimed_by_user_id (Integer FK → users.id) — кто забрал ghost-профиль
- is_claimed (Boolean) — заблокирован от редактирования

ЭНДПОИНТЫ БЭКЕНДА:
- GET /api/players/{ghost_id}/can-claim — можно ли заявить (BattleTag совпадает?)
- POST /api/players/{ghost_id}/claim — создать заявку
- GET /api/admin/claims — список заявок (admin)
- POST /api/admin/claims/{id}/approve — одобрить + merge (admin)
- POST /api/admin/claims/{id}/reject — отклонить с комментарием (admin)

ФРОНТЕНД:
- Кнопка "Это мой профиль" на странице ghost-профиля
- После нажатия: "Заявка отправлена, ждём одобрения админа"
- Админка: вкладка "Заявки на профили" с таблицей

БЭКЕНД — ПОДКЛЮЧЕНИЕ ПРОФИЛЯ К БД:
Текущие эндпоинты:
- GET /api/players/{id} — User + battletags (PlayerProfileResponse)
- GET /api/players/{id}/tournaments — список турниров игрока
- MatchPlayer: eliminations, deaths, hero_damage_dealt, healing_dealt, damage_blocked, contribution_score, is_mvp, is_svp, last_hero, time_played
- MatchPlayerHero: per-hero stats (eliminations, damage, healing, deaths, time_played, weapon_accuracy и т.д.)
- MatchKill: kills с is_first_blood

ФОРМУЛЫ РАСЧЁТОВ (из логов):
- Contribution Score: elim*500 + fb*250 + assists*50 + hero_dmg + healing - deaths*750 + blocked*0.1
- KDA: (eliminations + assists) / max(deaths, 1)
- Winrate: wins / total_encounters * 100
- Playtime: SUM(time_played) / 3600
- MVP Score: AVG(contribution_score WHERE is_mvp=1)
- SVP Score: AVG(contribution_score WHERE is_svp=1)
- Hero stats: SUM(per-hero stats) GROUP BY hero_name

ЧТО НУЖНО ДОБАВИТЬ В БЭКЕНД:
1. Эндпоинт GET /api/players/{id}/profile-stats — агрегированная статистика
2. Эндпоинт GET /api/players/{id}/top-heroes — топ-3 героя
3. Расширить PlayerProfileResponse полями: tournaments_count, wins_count, winrate, primary_role, playtime, maps_count
4. Логика Place — ранжирование участников турнира

ТЕКУЩИЕ TODO:
- Вкладка HISTORY на странице турнира
- Вкладка SCHEDULE на странице турнира
- Вкладка КОМАНДЫ в дашборде
- Авто-создание команд после драфта
- Автоматическое продвижение победителя в сетке
- Подключение реальных данных к PlayerProfile (сейчас демо)
- Profile Claim System (описано выше)

ТЕХНИЧЕСКИЕ ДЕТАЛИ:
- Админ: user_id=79, username=yebvaiotsuda, role=admin
- Docker: 4 контейнера (backend:8000, frontend:5173, db:5432, redis:6379)
- 6 турниров в БД, 75 матчей, 59 встреч, 64 участника, 12 команд, 5094 kills
- СЕСИЯ ДРАФТА — ПОЛНЫЙ ДАМП ВСЕХ ИЗМЕНЕНИЙ (апрель 2026):

BACKEND — draft_service.py:
- make_pick(db, redis_client, session_id, pick_data, current_user_id, is_admin=False) — is_admin в КОНЦЕ с дефолтом
- Проверка очереди: if not is_admin and current_picker_id != current_user_id → 403
- setup_draft_session — находит капитанов через TournamentParticipant.is_captain=True + status="registered", создаёт DraftCaptain записи

BACKEND — draft_public.py:
- POST /api/draft/{session_id}/pick — is_admin = current_user.role == "admin", передаёт в make_pick

BACKEND — dev.py:
- POST /api/dev/tournaments/{id}/seed-participants — создаёт 10 участников, первые 2 с is_captain=True + status="registered", остальные 8 is_captain=False + status="registered"
- POST /api/dev/tournaments/{id}/reset-draft — удаляет DraftPick, DraftCaptain, DraftSession, сбрасывает статус турнира на "registration"
- DELETE /api/dev/tournaments/{id}/participants — удаляет все TournamentParticipant (не User), возвращает count

BACKEND — tournaments.py:
- GET /api/tournaments/ — добавлен selectinload(Tournament.draft_session) для MissingGreenlet фикса

FRONTEND — TournamentAdminDashboard.jsx:
- handleResetDraft — confirm → resetDraft API → alert → reload
- handleDeleteAllParticipants — confirm → deleteAllParticipants API → alert count → reload
- handleSingleApprove/Reject, handlePromote/Demote — добавлен finally {} (фикс вечной загрузки)
- 3 dev-кнопки в flex-контейнере: "Заполнить участниками", "Сбросить драфт", "Удалить всех участников" (все admin-btn--danger)
- Кнопка 👑 показывается для ВСЕХ approved (status="registered"), нет проверок is_bot или user_id

FRONTEND — DraftPlayerPool.jsx:
- Убран alert("In a real app...") — handlePick сразу вызывает makePick
- displayName обрезает до 16 символов + '...'
- isMyTurn: currentUser.role === 'admin' → true (админ кликает в любой ход)

FRONTEND — DraftTimer.jsx:
- teamName/captainName обрезаются до 16 + '...'

FRONTEND — DraftTeamsPanel.jsx:
- truncateName хелпер (16 + '...')
- className="team-name" и "captain-name" для CSS обрезки

FRONTEND — DraftPage.css:
- .draft-page * { font-family: 'Ponter', sans-serif !important; }
- grid: repeat(auto-fill, minmax(240px, 1fr)), gap: 1.5rem, overflow-x: hidden, width: 100%
- .player-card: min-height: 120px, justify-content: space-between
- .team-name/.captain-name: overflow hidden, text-overflow ellipsis, white-space nowrap, max-width 150px
- .player-card-name: overflow hidden, text-overflow ellipsis, white-space nowrap, max-width 100%

FRONTEND — dev.js:
- seedParticipants, resetDraft, deleteAllParticipants

FRONTEND — useDraft.js:
- makePick — POST /draft/${sessionId}/pick через draftApi
- .finally(() => setLoading(false)) в начальной загрузке
- ИСПРАВЛЕНИЕ СЕТКИ ДРАФТА — карточки наезжали друг на друга:
- .draft-pool-container: min-width:0 + overflow:hidden (фикс выхода за grid-колонку)
- .draft-pool-container .player-pool-header: flex-shrink:0
- .draft-pool-container .player-pool-grid: flex:1 + min-height:0 (растягивается и скроллится)
- .draft-teams-container: min-width:0
- grid: repeat(auto-fill, minmax(260px, 1fr)), gap:1.5rem
- .player-card: min-height:120px, width:100%, box-sizing:border-box
- Убран дублирующийся .player-card блок в конце CSS

## PLAYER PROFILE (Новая верстка — 9 CSS файлов)
**PlayerProfile.jsx** — страница профиля игрока с pixel-perfect версткой по макету Kleiner

### CSS файлы:
- **PlayerProfile.css** — корневой layout: `.profile-main { min-width:1700px, max-width:1920px }`, grid `450px 1fr`, `.profile-layout { align-items:end }`, `.profile-divider` линия, responsive breakpoints
- **PlayerCard.css** — карточка игрока 450×255px, clip-path скос 30px, `border-left:4px`, аватар 100×100px, battletag-row 130×25px + badge +8, twitch-row, player-divider, stat-blocks с margin-left 0/30/30px
- **AchievementsCard.css** — 450×160px, иконки 55×55px gap 12px, clip-path + ::after диагональ
- **DivisionsCard.css** — иконки div6_Images/div14_Images PNG 80×80px, gap 35px, подписи "♥ TANK / !!! DPS / + SUP"
- **ProfileTabs.css** — `.profile-tab.active { background:rgba(167,242,162,0.08) }`, подчёркивание через ::after bottom:-5px (отрывается от линии контейнера)
- **FilterRow.css** — tournament-select 325×40px, playtime/maps иконки SVG, `.win-lose-pill { clip-path:polygon(16px 0%,...) margin-left:auto }`, WIN=#13AD91 LOSE=#A7F2A2
- **StatsTopRow.css** — 4×265px карточки, PLACE: 12 и PLACE оба 36px baseline gap 10px, MVP/SVP лейблы 30px #13AD91, значения #A7F2A2, ::after диагональная линия скоса
- **StatsBottomRow.css** — 4×265×160px карточки, padding 30px 30px 30px 74px (учёт gradient), ::before gradient 10×100px, ::after диагональная линия
- **TopHeroesCard.css** — header + divider + content, hero-block grid 1fr auto, hero-separator 1px между героями, hero-avatar-wrapper с hero-avatar-line 3px, avatar 100×100px border 2px #A7F2A2, hero-stats-grid 2×2 (105×65px), label 10px

### Иконки героев:
`/public/assets/icons_hero/` — 50 PNG файлов (Icon-Mercy.png, Icon-Genji.png, Icon-D.Va.png, Icon-Ana.png и др.)
Демо-данные в topHeroes массиве: MERCY, GENJI, D.VA с путями к реальным PNG

### Clip-path скосы — диагональная линия ::after ВЕЗДЕ:
PlayerCard, AchievementsCard, DivisionsCard, tournament-history-card, stat-card-small, stat-card-large, top-heroes-card, hero-block — на каждом элементе с clip-path есть ::after с rotate(45deg) для видимой диагонали #13AD91

### Цветовая логика PlayerProfile:
Лейблы (MVP SCORE/SVP SCORE/PLACE) = #13AD91
Значения и sub-тексты = #A7F2A2
Фон активной вкладки = rgba(167,242,162,0.08)

## МНОГОЭТАПНАЯ СИСТЕМА ТУРНИРОВ (Backend)
### Модели: TournamentStage, StageGroup (enum: StageFormat, SeedingRule)
### Сервис: stage_service.py — generate_stage_matches (RR/Swiss/SE/DE), advance_to_next_stage (UPPER_LOWER_SPLIT, CROSS_GROUP_SEEDING)
### API: /api/stages/ — CRUD stages/groups, generate-matches, advance, participant assignment
### Миграция: 010_stages_and_groups.py (raw SQL)
### Тесты: 6/6 PASSED (tests/test_stage_service.py)
### Фронтенд: StageBuilder.jsx + StageParticipantsManager.jsx интегрированы в AdminTournamentForm

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Шрифты: 'Digits' (ST-SimpleSquare), 'Ponter', 'Arial Black'
- CSS переменные: --tournament-accent:#13AD91, --tournament-accent-light:#A7F2A2, --block-bg:#111B25, --button-bg:#23423F
- Админ: user_id=79, username=yebvaiotsuda, role=admin
- Docker: 4 контейнера (backend:8000, frontend:5173, db:5432, redis:6379)

## НОВЫЕ МОДЕЛИ БД
- **TournamentStage**: id, tournament_id, stage_number, name, format (ROUND_ROBIN/SWISS/SINGLE_ELIMINATION/DOUBLE_ELIMINATION), settings (JSONB: stage_config + advancement_config)
- **StageGroup**: id, stage_id, name
- **TournamentParticipant**: добавлены group_id (FK → stage_groups), seed (INTEGER)
- **Encounter**: добавлен stage_id (FK → tournament_stages), поле stage переименовано в stage_name
- **Enums**: stage_format, seeding_rule (CROSS_GROUP_SEEDING/UPPER_LOWER_SPLIT)

## СЕРВИСЫ
- **stage_service.py**: generate_stage_matches (ROUND_ROBIN, SWISS, SINGLE/DOUBLE_ELIMINATION), advance_to_next_stage (UPPER_LOWER_SPLIT, CROSS_GROUP_SEEDING), _calculate_final_rankings, _apply_upper_lower_split, _apply_cross_group_seeding

## API ENDPOINTS (/api/stages/)
- POST / — создание этапа
- GET /tournament/{id} — список этапов
- GET /{id} — детали этапа
- PUT /{id} — обновление
- DELETE /{id} — удаление
- POST /{id}/generate-matches — генерация матчей
- POST /{id}/advance — продвижение к следующему этапу
- POST /{id}/groups — создание группы
- GET /{id}/groups — список групп
- POST /groups/{id}/participants/{pid} — назначение участника
- POST /groups/{id}/participants/bulk — массовое назначение

## ФРОНТЕНД КОМПОНЕНТЫ
- **StageBuilder.jsx**: конструктор этапов (добавление/удаление/настройка), настройки перехода появляются только если есть следующий этап
- **StageParticipantsManager.jsx**: drag-and-drop для Round Robin (группы), упорядоченный список для Elimination (посев), массовое назначение
- Интегрировано в AdminTournamentForm.jsx

## МИГРАЦИИ
- 010_stages_and_groups.py — raw SQL миграция (таблицы tournament_stages, stage_groups, колонки group_id/seed/stage_id)
- Примечание: миграция была "заштампована", колонки добавлены вручную через ALTER TABLE

## ТЕСТЫ
- tests/test_stage_service.py — 6 тестов (UPPER_LOWER_SPLIT, CROSS_GROUP_SEEDING, Round Robin combinations) — все PASSED

## ИСПРАВЛЕНИЯ
- Encounter.stage (строка) → Encounter.stage_name, relationship переименован в stage_ref
- volumes для фронтенда раскомментированы в docker-compose.yml
- Админ: user_id=79, username=yebvaiotsuda, role=admin

## АРХИТЕКТУРА
- Бэкенд: FastAPI + SQLAlchemy async + PostgreSQL 16 + Redis 7
- Фронтенд: React 18 + Vite + Axios + React Router
- Docker Compose: 4 контейнера (backend:8000, frontend:5173, db:5432, redis:6379)
- Прокси Vite: /api → http://backend:8000 с followRedirects

## МОДЕЛИ БД (backend/app/models/)
1. **Tournament** — 25+ полей: title, format (mix/draft/other), description_general/dates/requirements, start/end dates, registration/checkin windows, status, max_participants, participants_count, is_featured, is_active, structure_type (SINGLE_ELIMINATION/DOUBLE_ELIMINATION/ROUND_ROBIN/GROUPS_PLUS_PLAYOFF/SWISS), structure_settings (JSON), twitch_channel, rules_url
2. **TournamentParticipant** — заявки: user_id, status (pending/registered/rejected), is_allowed, application_data (JSON), checkedin_at
3. **User** — discord_id, username, display_name, avatar_url, role (player/admin), primary_role, secondary_role, bio, is_banned, reputation_score, is_ghost
4. **BattleTag** — user_id, tag, is_primary
5. **Team** — tournament_id, name, captain_user_id
6. **Encounter** — tournament_id, team1_id, team2_id, team1_score, team2_score, winner_team_id, stage, round_number, is_auto_created
7. **Match** — encounter_id, tournament_id, team1_id, team2_id, winner_team_id, map_name, game_mode, duration_seconds, file_hash, file_name, round_stats (JSON)
8. **MatchPlayer** — match_id, user_id, player_name, team_id, eliminations, final_blows, deaths, all_damage_dealt, hero_damage_dealt, healing_dealt, damage_blocked, contribution_score, is_mvp, is_svp, last_hero + 15+ метрик
9. **MatchPlayerHero** — match_player_id, hero_name, eliminations, final_blows, deaths, damage, healing, weapon_accuracy, time_played + 25+ метрик
10. **MatchKill** — match_id, killer/victim (name+hero+team+user_id), weapon, damage, is_critical, is_headshot, timestamp, round_number, offensive_assists (JSON), defensive_assists (JSON), is_first_blood
11. **DraftSession** — tournament_id, status (pending/in_progress/completed), pick_time_seconds, team_size, current_pick_index, pick_order (JSON), role_slots (JSON), current_pick_deadline
12. **DraftCaptain** — draft_session_id, user_id, team_name, pick_position, captain_role
13. **DraftPick** — draft_session_id, captain_id, picked_user_id, pick_number, round_number, assigned_role, is_auto_pick

## ENDPOINTS (backend/app/routers/)
**Tournaments** (/api/tournaments/):
- GET / — список с фильтрацией
- GET /{id} — детали
- POST / — создание (admin)
- PUT /{id} — обновление (admin)
- DELETE /{id} — удаление (admin)
- PATCH /{id}/status — смена статуса (admin)
- GET /{id}/bracket — сетка турнира
- GET /{id}/participants — одобренные участники (публичный)
- GET /{id}/my-status — статус моей заявки
- POST /{id}/register/mix — заявка mix
- POST /{id}/register/draft — заявка draft
- POST /{id}/checkin — check-in
- GET /{id}/applications — заявки (admin, с фильтром)
- POST /{id}/applications/{user_id}/approve — одобрить (admin)
- POST /{id}/applications/{user_id}/reject — отклонить (admin)
- POST /{id}/applications/approve-bulk — массовое одобрение (admin)
- POST /{id}/applications/reject-bulk — массовое отклонение (admin)

**Draft** (/api/admin/draft/ и /api/draft/):
- POST /{tournament_id}/setup — настройка сессии (admin)
- POST /{session_id}/start — запуск драфта (admin)
- POST /{session_id}/pick — капитан делает пик
- GET /{session_id} — состояние драфта
- WS /ws/draft/{session_id} — real-time обновления

**Matches** (/api/matches/):
- POST /teams — создать команду (admin)
- GET /teams/tournament/{id} — команды турнира
- POST /encounters — создать encounter (admin)
- GET /encounters/tournament/{id} — encounters турнира
- GET /encounters/{id} — детали encounter
- POST /upload — загрузка лога (CSV parsing)
- GET /{match_id} — детали матча
- GET /{match_id}/killfeed — kill feed
- GET /{match_id}/first-blood — first blood каждого раунда
- GET /player/{user_id}/history — история матчей игрока
- DELETE /{match_id} — удалить матч (admin)
- PUT /admin/encounters/{id}/result — ручной ввод результата (admin)
- PUT /admin/encounters/{id}/forfeit — тех. поражение (admin)
- PUT /admin/encounters/{id}/replace — замена команды (admin)
- DELETE /admin/encounters/{id} — удаление встречи (admin)
- POST /admin/tournaments/{id}/swiss-next-round — следующий тур швейцарки (admin)

**Auth** (/api/auth/):
- GET /discord — редирект на Discord OAuth
- GET /discord/callback — callback + JWT
- POST /token — тестовая генерация
- GET /me — инфо текущего пользователя

**Users** (/api/users/):
- GET /me/battletags — мои BattleTag'и
- GET /me — мой профиль
- GET /me/applications — все мои заявки

**Players** (/api/players/):
- GET / — список игроков
- GET /{id} — профиль
- GET /{id}/tournaments — история турниров
- PUT /{id} — редактировать
- DELETE /{id} — удалить

## СЕРВИСЫ (backend/app/services/)
1. **tournament_service.py** — CRUD турниров, get_bracket, update_status
2. **draft_service.py** — setup_draft_session, start_draft (Redis deadline + PubSub), make_pick (with_for_update), get_draft_state
3. **match_service.py** — create_team, create_encounter, upload_log (полный пайплайн: CSV parsing → player resolution → team mapping → Match/MatchPlayer/MatchPlayerHero/MatchKill → Contribution Score → MVP/SVP → First Blood → Encounter score update), update_encounter_result, set_encounter_forfeit, replace_team_in_encounter, delete_encounter, generate_swiss_next_round
4. **match_metrics.py** — calculate_contribution_score (elim*500 + fb*250 + assists*50 + hero_dmg + healing - deaths*750 + blocked*0.1), assign_mvp_svp, determine_first_bloods, get_last_hero, compute_match_metrics
5. **log_parser.py** — парсинг CSV логов: match_start/end, round_start/end, kill, offensive/defensive_assist, player_stat; round-by-round stats через diff() cumulative; kill feed с assists matching (1 сек окно)

## ФРОНТЕНД (frontend/src/)
**Страницы:**
- Home.jsx — главная
- Tournaments.jsx — список турниров с фильтрами (ALL/MIX/EVENT/DRAFT)
- TournamentDetail.jsx — страница турнира (вкладки: information/bracket/participants/history/schedule)
- TournamentAdminDashboard.jsx — ЦЕНТР УПРАВЛЕНИЯ ТУРНИРОМ (вкладки: заявки/команды/сетка/управление)
- AdminApplications.jsx — админка заявок (таблица, фильтры, approve/reject)
- AdminTournamentsList.jsx — список турниров в админке
- AdminTournamentForm.jsx — создание/редактирование турнира
- AdminMatchUpload.jsx — загрузка логов
- DraftPage.jsx — страница драфта (таймер, пул игроков, составы команд, WebSocket)
- MatchDetail.jsx — детали матча
- EncounterDetail.jsx — детали encounter
- PlayerProfile.jsx — профиль игрока
- PlayerProfileEdit.jsx — редактирование профиля
- PlayersList.jsx — список игроков
- AuthCallback.jsx — обработка OAuth

**Компоненты:**
- bracket/InteractiveBracket.jsx — единый интерактивный интерфейс сетки (посев random/manual, drag-and-drop, визуальная сетка раундов, список швейцарки, клик → модалка)
- tournament/bracket/BracketStage.jsx, MatchCard.jsx — публичная сетка
- draft/DraftPlayerPool.jsx, DraftTeamsPanel.jsx, DraftTimer.jsx
- match/KillFeed.jsx
- RegisterModal/, RoleSelector/, BattleTagSelector/, ConfirmModal/

**API-клиенты:**
- tournaments.js — getAll, getById, getMyStatus, registerForMix/Draft, checkin, create/update/delete, updateStatus, getApplications, approve/reject (single+bulk), getParticipants
- draft.js — getState, makePick
- matches.js — CRUD команд/encounters, upload log, get match/killfeed/first-blood, player history
- players.js, auth.js, client.js (axios с baseURL: '/api' и interceptor для токена)

**Роутинг (App.jsx):**
Публичные: /, /tournaments, /tournaments/:id, /players, /players/:id, /players/:id/edit, /auth/callback, /draft/:tournamentId, /matches/:id, /encounters/:id
Админские (AdminRoute): /admin/homepage, /admin/tournaments, /admin/tournaments/new, /admin/tournaments/:id/edit, /admin/matches/upload, /admin/tournaments/:tournamentId/applications, /admin/tournaments/:id/dashboard

## КЛЮЧЕВЫЕ ФИЧИ
1. ✅ Discord OAuth2 аутентификация + JWT
2. ✅ Регистрация на mix/draft турниры с BattleTag
3. ✅ Админка заявок с фильтрацией и bulk approve/reject
4. ✅ Draft система с WebSocket real-time (Redis PubSub)
5. ✅ Загрузка CSV логов с полным парсингом (stats, kills, assists)
6. ✅ Contribution Score, MVP/SVP, First Blood
7. ✅ Kill Feed с assists matching
8. ✅ Интерактивная сетка: посев (random/manual drag-and-drop), визуальное дерево раундов, клик → модалка (загрузка лога/ввод счёта/forfeit/замена команды/удаление)
9. ✅ Швейцарская система: авто-генерация раундов по счёту с избеганием повторных матчей
10. ✅ Дедупликация пользователей (77 дубликатов удалены)
11. ✅ Vite proxy с followRedirects для обхода 307 редиректов FastAPI
12. ✅ 6 турниров в БД, 75 матчей, 59 встреч, 64 участника, 12 команд, 5094 kills

## ТЕКУЩИЕ ЗАГЛУШКИ / TODO
- Вкладка HISTORY на странице турнира (показать таблицу матчей)
- Вкладка SCHEDULE на странице турнира
- Вкладка КОМАНДЫ в дашборде (drag-and-drop формирование команд для MIX)
- Авто-создание команд после завершения драфта (DraftPick → Team)
- Автоматическое продвижение победителя в следующий раунд (SE/DE bracket)
- Блок с итоговыми местами (1-е, 2-е, 3-е)
- Посев по рейтингу

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Кодировка UTF-8 в БД и скриптах
- Ghost-профили для игроков из логов (без Discord)
- bulk_import.py — авто-импорт 76 логов в турнир
- seed_tournaments.py — 6 тестовых турниров
- tournament_config.json — конфигурация команд для импорта
- Админ: user_id=79, username=yebvaiotsuda, role=admin

## Дизайн вкладки УЧАСТНИКИ (Participants) — страница турнира

### Расположение
Страница `/tournaments/:id`, вкладка PARTICIPANTS. Подвкладки: УЧАСТНИКИ / КОМАНДЫ.

### БЛОК 1 — Суб-вкладки (УЧАСТНИКИ / КОМАНДЫ)
- Высота контейнера: 45px, ширина 280px
- Горизонтальный padding текста: 13px
- Шрифт: ST-SimpleSquare, высота 19px
- Цвет текста неактивной: прозрачный
- Цвет текста активной: #23423F
- Подчёркивание активной: толщина 5px, цвет #A7F2A2
- Нижняя линия под вкладками: толщина 2px, цвет #13AD91
- Отступ от суб-вкладок до контента: 30px

### БЛОК 2 — Панель управления (Поиск + Фильтры)
**Поиск:**
- Ширина 325px, высота 40px
- Фон: #111B25, рамка: 1px #13AD91
- Padding: слева от лупы 17px, от лупы до текста 16px
- Шрифт: Ponter, 18px, цвет плейсхолдера: #A7F2A2 ("ПОИСК УЧАСТНИКА...")

**Кнопки ролей (ALL, TANK, DPS, SUP, FLEX):**
- Высота: 30px, горизонтальный padding: 6px
- Border-radius: 3px
- Активная: фон + текст #13AD91
- Неактивная: фон + текст #23423F

### БЛОК 3 — Сетка карточек (Grid)
- Gap: 20px по горизонтали и вертикали
- Нет общей рамки вокруг всех карточек

### БЛОК 4 — Карточка участника
**Общее:**
- Размер: 345×240px
- Фон: #111B25, обводка: #13AD91
- Внутренний padding: 25px
- Срезанные углы: левый верхний и правый нижний, 20px
- Полоска слева: 5px, цвет #13AD91
- Hover: появляется рамка 1px, цвет #13AD91

**Шапка (Цифра + Роль):**
- Цифра: ST-SimpleSquare, 17px, цвет #A7F2A2
- Бейдж роли: 65×30px, прозрачный фон, обводка 1px #A7F2A2, padding 7px
- Текст бейджа: Ponter, 15px, цвет #A7F2A2

**Инфо об игроке:**
- Аватар: 45×45px, рамка 1px #A7F2A2
- Расстояние аватар → BattleTag: 16px
- BattleTag: Ponter, 15px, цвет #13AD91
- Discord-имя: Ponter, 11px, расстояние иконка→текст 6px

**Био:**
- Шрифт: Montserrat Medium, 11px, цвет #13AD91
- Line-height: 10px
- Максимум 3 строки
- Отступ имя→био: 51px, био→подвал: 16px

**Подвал (Статусы):**
- CHECK-IN: Ponter, 15px. Активный: #A7F2A2, неактивный: #23423F
- ALLOWED/NOT ALLOWED: Ponter, 15px. Allowed: #A7F2A2, Not Allowed: #23423F

---

## ОБНОВЛЕНИЯ ПРОЕКТА (Сессия 2026-04-13+)

### 1. СИСТЕМА КАПИТАНОВ + АВТО-СОЗДАНИЕ КОМОД ПОСЛЕ ДРАФТА

**Модели БД:**
- `TournamentParticipant`: добавлены `is_captain` (Boolean), `team_id` (FK → teams.id)
- `DraftPick`: добавлен `team_id` (FK → teams.id)
- `Team`: добавлены `draft_picks`, `tournament_participants` relationships

**Миграции:**
- `011_add_is_captain_to_participant.py` — is_captain в tournament_participants
- `012_add_team_id_to_draft_picks.py` — team_id в draft_picks
- `013_add_team_id_to_participants.py` — team_id в tournament_participants

**Сервисы:**
- `tournament_service.py`: `set_captain_status()`, `get_tournament_captains()`
- `draft_service.py`: `complete_draft_session()` — поддержка N команд, группирует picks по captain_id, создаёт Team, обновляет team_id для DraftPick и TournamentParticipant
- `draft_service.py` — `setup_draft_session()` обновлён: сначала ищет капитанов через `is_captain=True`, fallback на legacy captain_user_ids
- `make_pick()` — авто-вызов `complete_draft_session()` после последнего пика

**Эндпоинты:**
- `POST /api/tournaments/participants/{id}/promote` — назначить капитаном (admin)
- `POST /api/tournaments/participants/{id}/demote` — снять капитана (admin)
- `GET /api/tournaments/{id}/captains` — список капитанов турнира
- `POST /api/admin/draft/{session_id}/complete` — ручное завершение драфта (admin)

**Фронтенд:**
- `tournaments.js` — `promoteParticipant()`, `demoteParticipant()`
- `ApplicationsTab` — кнопки 👑/👑✕ для одобренных участников, бейдж капитана у ника
- `useDraft.js` — обработчики WS: `draft_completed`, `draft_started`
- `draft.js` — `completeDraft()`
- `DraftPage.jsx` — кнопка "Завершить драфт" (только админ, статус in_progress)

### 2. SINGLE-ELIMINATION АВТО-ПРОДВИЖЕНИЕ

**Модели:**
- `Encounter`: добавлен `next_encounter_id` (FK → encounters.id), relationship `next_encounter`

**Миграции:**
- `014_add_next_encounter_id.py` — next_encounter_id в encounters

**Сервисы:**
- `match_service.py`: `report_encounter_result()` — определяет победителя, обновляет счёт, продвигает winner в `next_encounter` (team1_id или team2_id — первый свободный слот)
- `_encounter_to_dict()` — добавлен `next_encounter_id`

**Эндпоинты:**
- `PUT /api/matches/admin/encounters/{id}/report-result` — сообщить результат + авто-продвижение (admin)

**Фронтенд:**
- `matches.js` — `reportEncounterResult()`
- `InteractiveBracket.jsx` — MatchBlock с кнопкой ✏️ (только админ), модальное окно ввода счёта
- `TournamentAdminDashboard.jsx` — `onEncounterUpdated={loadEncounters}` для авто-обновления

### 3. API URL REFACTORING

- Убраны все `/api/` префиксы из `frontend/src/api/*.js`
- `client.js` имеет `baseURL: '/api'`, все пути относительные
- `auth.js` — переписан с прямого axios на `client`

### 4. TOURNAMENT CREATION FIX (500 error)

- `AdminTournamentForm.jsx` — явная передача `tournament_id` в payload этапа
- `stages.py` — добавлен `.unique()` для всех запросов с `joinedload(TournamentStage.groups)` (4 места: create, get, get_by_id, update)
- `TournamentResponse` schema — добавлено поле `draft_session: Optional[DraftSessionResponse]`
- `_get_tournament_or_404()` — добавлен `selectinload(Tournament.draft_session)`

### 5. DEV SEED ENDPOINT

- `backend/app/routers/dev.py` — `POST /api/dev/tournaments/{id}/seed-participants`
- `config.py` — добавлено `ENVIRONMENT: str = "development"`, guard: в production → 403
- `main.py` — условное подключение dev роутера: `if settings.ENVIRONMENT != "production"`
- `ManagementTab` — секция "🛠 Dev-инструменты", кнопка "Заполнить участниками (Dev)"

### 6. DRAFT START + AUTO-NAVIGATION

- `draft.js` — добавлены `setupDraft()`, `startDraft()`
- `ManagementTab` — секция "🎤 Драфт" с кнопками: "⚙️ Настроить и запустить", "▶️ Запустить", "🎯 Перейти к драфту"
- `handleStartDraft()` — загружает капитанов → setup_draft → start_draft → `navigate(/draft/{tournamentId})`
- `DraftPage.jsx` — **убран хардкод `sessionId = 2`**, теперь читает `tournamentId` из URL, загружает турнир → `tournament.draft_session.id`

### 7. КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ В АРХИТЕКТУРЕ

**Поток драфта:**
1. Админ назначает капитанов (👑) на вкладке "ЗАЯВКИ"
2. Вкладка "УПРАВЛЕНИЕ" → "⚙️ Настроить и запустить драфт"
3. Бэкенд: `setup_draft_session` (ищет капитанов через `is_captain=True`) → `start_draft`
4. Авто-редирект на `/draft/{tournamentId}`
5. Страница драфта загружает турнир → извлекает `draft_session.id`
6. Капитаны делают пики → после последнего пика авто-вызов `complete_draft_session`
7. Создаются Team, обновляются team_id → WS `draft_completed`

**Поток single-elimination:**
1. Админ создаёт encounters с `next_encounter_id` (match 1→3, match 2→3)
2. ✏️ на матче → ввод счёта → `report_encounter_result`
3. Победитель автоматически попадает в `next_encounter.team1_id` или `team2_id`
4. Сетка автоматически обновляется

**API client паттерн:**
- Все запросы через `client` (axios, baseURL='/api')
- Пути БЕЗ `/api/` префикса и БЕЗ trailing slash
- Пример: `client.get('/draft/${sessionId}')` → `/api/draft/{sessionId}`

## СЕССИЯ ОБНОВЛЕНИЙ (2026-04-14 — полный дамп всех изменений за день)

### 1. ИСПРАВЛЕНИЕ UVICORN RELOAD (Зависание при перезагрузке)
**Проблема:** uvicorn зависал на "Waiting for background tasks to complete" при изменении .py файлов.

**Решение:**
- `backend/Dockerfile` — добавлен `--timeout-graceful-shutdown 5` в CMD uvicorn
- `backend/app/main.py` — добавлен shutdown handler: `await engine.dispose()` для корректного закрытия соединений БД

**Результат:** Перезагрузка за 3-5 сек, без зависаний.

### 2. TAB "КОМАНДЫ" — ПОЛНАЯ РЕАЛИЗАЦИЯ (E2E-тест драфт→команды→сетка)
**Backend:**
- `schemas/match.py` — расширена `TeamResponse` (participants, captain), добавлены `TeamBriefResponse`, `TeamParticipantBrief`, `UserBrief`
- `services/match_service.py` — `get_teams_by_tournament` с selectinload(team1_participants, captain)
- `routers/matches.py` — явное преобразование Team → TeamResponse с вложенными данными

**Frontend:**
- `TournamentAdminDashboard.jsx` — переписан `TeamsTab`: загрузка через API, карточки команд с 👑 капитаном, список участников, кнопка "Обновить"
- `TournamentAdminDashboard.css` — стили: .admin-team-card, .admin-team-header, .admin-team-players, text-overflow: ellipsis

### 3. FIX 500 — ГЕНЕРАЦИЯ СЕТКИ (stage vs stage_name)
**Проблема:** `TypeError: 'stage' is an invalid keyword argument for Encounter`

**Решение:** Поле `stage` переименовано в `stage_name` в модели Encounter, но код использовал старое имя.
- `services/match_service.py` — `stage=data.stage` → `stage_name=data.stage` в create_encounter
- `routers/matches.py` — `encounter.stage` → `encounter.stage_name` в response

### 4. FIX 500 — GET ENCOUNTERS (MissingGreenlet)
**Проблема:** Pydantic пытался загрузить `team.captain` после закрытия сессии → MissingGreenlet

**Решение:** Создана `TeamBriefResponse` (без captain/participants) для EncounterResponse. Компромисс: TeamResponse (полная) используется для GET teams, TeamBriefResponse (упрощённая) — для GET encounters.

### 5. FIX 404 — REPORT RESULT (неправильный URL)
**Проблема:** Фронтенд вызывал `/result/` вместо `/report-result`, + trailing slash → 307 redirect

**Решение:**
- `TournamentAdminDashboard.jsx` — `/result/` → `/report-result` (без trailing slash)
- `matches.js` — `/report-result/` → `/report-result`
- Глобальный поиск подтвердил: нет ни одного вызова `/result/`, `/draft/tournament/`

### 6. FIX 500 — REPORT_ENCOUNTER_RESULT (ещё раз stage → stage_name)
**Проблема:** `_encounter_to_dict()` использовал `enc.stage` вместо `enc.stage_name`

**Решение:** `services/match_service.py` строка 862 — `'stage': enc.stage_name`

### 7. ПУБЛИЧНАЯ СЕТКА ТУРНИРА (read-only)
**Изменения:**
- `bracket/BracketStage.jsx` — полностью переписан: убран MOCK_TOURNAMENT_DATA, загрузка через `client.get('matches/encounters/tournament/${id}')` + teams
- Функция `transformEncountersToRounds()` — конвертация encounters → rounds формат
- Авто-обновление каждые 30 сек (setInterval)
- Состояния: Loading / Error / Empty ("Сетка ещё не сгенерирована")
- Нет админских кнопок — чисто информационный компонент

### 8. ПЕРЕНОС ДЛИННОГО НАЗВАНИЯ ТУРНИРА
**Проблема:** `.td-sidebar-name` имел `white-space: nowrap` — длинное название уходило за пределы контейнера.

**Решение:** `TournamentDetail.css` — `.td-sidebar-name`: `white-space: normal`, `overflow-wrap: break-word`, `word-break: break-word`, `line-height: 1.2`

### 9. УГОЛКИ ИКОНОК В ХЕДЕРЕ (corner-icon-link)
**Эволюция:**
1. Сплошная рамка `border: 1px solid var(--accent)` → убрана
2. Псевдо-элементы с `transform: scaleX(0.25)` → создавали "прицел" вместо уголков
3. 4 уголка через `<span>` + ::before/::after на родителе и span → слишком сложно
4. **Финал: 2 уголка** (правый-верхний + левый-нижний) через 2 псевдо-элемента на `<a>`

**CSS:**
```css
.corner-icon-link::before { /* правый-верхний: border-top + border-right */ }
.corner-icon-link::after  { /* левый-нижний: border-bottom + border-left */ }
```
- Размер: 24×16px (прямоугольные)
- Hover: `width/height: 100%` — уголки смыкаются в полную рамку

### 10. REUSABLE CORNER-ICON-CLASS
**Общий класс:** `.corner-icon-link` (в `home.css`)
**Применён в:** `Header.jsx` (4 иконки) + `Footer.jsx` (5 иконок)
**Удалено:** старые `.home-social`, `.home-footer-social` стили

### 11. КНОПКА "MY PROFILE" — ОТКРЫТАЯ РАМКА
**Проблема:** Сплошная рамка `border: 1px solid var(--accent)`

**Решение:** `home.css` — `.home-profile-btn`:
- Убрана `border`, `background: transparent`
- `::before` (правый-верхний): `width: 85%, height: 55%, border-bottom/left: none`
- `::after` (левый-нижний): `width: 85%, height: 55%, border-top/right: none`
- Hover: `width/height: 100%` — рамка замыкается

### 12. DEV TOOLS — ALLOW_TEST_ENDPOINT
**Изменение:** `.env` — добавлен `ALLOW_TEST_ENDPOINT=true` (исправлена слитая строка `FRONTEND_URL=...ALLOW_TEST_ENDPOINT=true`)

### КЛЮЧЕВЫЕ ПРАВИЛА (выведенные из отладки):
1. **Trailing slash** — всегда убирай в API вызовах (`client.get('matches/...')` без `/` на конце)
2. **stage → stage_name** — поле Encounter переименовано, ВСЕ обращения должны использовать `stage_name`
3. **TeamResponse vs TeamBriefResponse** — полная схема (с captain/participants) вызывает MissingGreenlet при lazy loading; для списков (encounters) используй упрощённую
4. **API URL паттерн** — БЕЗ `/api/` префикса (уже в baseURL client), БЕЗ trailing slash
5. **HMR** — Vite автоматически обновляет файлы, проверка через `docker logs moonrise-frontend --tail | hmr`
