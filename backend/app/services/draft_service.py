# app/services/draft_service.py
import json
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.models.draft import DraftSession, DraftCaptain
from app.models.tournament import Tournament, TournamentParticipant
from app.models.match import Team
from app.schemas.draft import DraftSetupRequest
from datetime import datetime, timedelta, timezone
import redis.asyncio as redis # Импортируем redis
from app.models.draft import DraftPick # Добавляем импор
from app.schemas.draft import DraftPickRequest # Добавляем импорт
from app.models.user import User
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app.schemas.draft import (
    DraftStateCaptain,
    DraftStatePick,
    DraftStatePlayer,
    DraftStateResponse
)

# Переписываем функцию на async
async def setup_draft_session(db: AsyncSession, tournament_id: int, setup_data: DraftSetupRequest):
    """
    Создать сессию драфта в статусе pending.

    Капитаны определяются двумя способами (оба работают):
    1. Через TournamentParticipant.is_captain=True (рекомендуемый способ)
    2. Через явный список captain_user_ids в setup_data (legacy)

    Args:
        db: сессия БД
        tournament_id: ID турнира
        setup_data: данные для настройки драфта

    Returns:
        Созданный объект DraftSession
    """
    # 1. Проверяем турнир
    result = await db.execute(select(Tournament).filter(Tournament.id == tournament_id))
    tournament = result.scalars().first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.format != "draft":
        raise HTTPException(status_code=400, detail="This tournament is not a draft format")

    existing_draft_res = await db.execute(select(DraftSession).filter(DraftSession.tournament_id == tournament_id))
    if existing_draft_res.scalars().first():
        raise HTTPException(status_code=400, detail="Draft session already exists")

    # 2. Определяем капитанов
    # Сначала пытаемся найти капитанов через is_captain
    captains_res = await db.execute(
        select(TournamentParticipant)
        .options(joinedload(TournamentParticipant.user))
        .filter(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.is_captain == True,
            TournamentParticipant.status == "registered"
        )
    )
    captain_participants = captains_res.scalars().all()

    # Если капитаны через is_captain не найдены — используем setup_data.captain_user_ids (legacy)
    if not captain_participants:
        captains_res = await db.execute(
            select(TournamentParticipant).filter(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.user_id.in_(setup_data.captain_user_ids),
                TournamentParticipant.status == "registered"
            )
        )
        captain_participants = captains_res.scalars().all()

        if len(captain_participants) != len(setup_data.captain_user_ids):
            raise HTTPException(status_code=400, detail="Some captains are not approved participants")

    # Извлекаем user_id капитанов
    captain_user_ids = [cp.user_id for cp in captain_participants]
    captain_user_ids_sorted = sorted(captain_user_ids)  # для консистентности

    # Guard: минимум 2 капитана для драфта
    if len(captain_user_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 2 captains for a draft, found {len(captain_user_ids)}. "
                   f"Assign captains via /participants/{{id}}/promote before setting up the draft."
        )

    # 3. ГЕНЕРАЦИЯ ЗМЕЙКИ
    pick_order = []
    for round_num in range(1, setup_data.team_size + 1):
        if round_num % 2 != 0:
            pick_order.extend(captain_user_ids)
        else:
            pick_order.extend(reversed(captain_user_ids))

    # 4. Создаем сессию драфта
    draft_session = DraftSession(
        tournament_id=tournament_id,
        status="pending",
        pick_time_seconds=setup_data.pick_time_seconds,
        team_size=setup_data.team_size,
        current_pick_index=0,
        pick_order=pick_order,
        role_slots=setup_data.role_slots
    )
    db.add(draft_session)
    await db.flush()

    # 5. Создаем капитанов
    for position, cap_user_id in enumerate(captain_user_ids, start=1):
        cap_participant = next((p for p in captain_participants if p.user_id == cap_user_id), None)
        if not cap_participant:
            raise HTTPException(status_code=400, detail=f"Captain with user_id={cap_user_id} not found")

        # Определяем имя команды: из setup_data или по имени игрока
        team_name = setup_data.team_names.get(cap_user_id, f"Команда {cap_user_id}")

        app_data = {}
        if cap_participant.application_data:
            try:
                app_data = json.loads(cap_participant.application_data)
            except (json.JSONDecodeError, TypeError):
                pass

        cap_role = app_data.get("primary_role", "flex")

        draft_captain = DraftCaptain(
            draft_session_id=draft_session.id,
            user_id=cap_user_id,
            team_name=team_name,
            pick_position=position,
            captain_role=cap_role
        )
        db.add(draft_captain)

    # 6. Меняем статус турнира
    tournament.status = "draft"

    await db.commit()
    return draft_session

async def start_draft(db: AsyncSession, redis_client: redis.Redis, session_id: int):
    # 1. Находим сессию драфта
    result = await db.execute(select(DraftSession).filter(DraftSession.id == session_id))
    draft_session = result.scalars().first()

    if not draft_session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    if draft_session.status != "pending":
        raise HTTPException(status_code=400, detail="Draft can only be started from 'pending' status")

    # 2. Проверяем что есть капитаны (DraftCaptain записи)
    captains_res = await db.execute(
        select(DraftCaptain).filter(DraftCaptain.draft_session_id == session_id)
    )
    captains = captains_res.scalars().all()
    if not captains:
        raise HTTPException(
            status_code=400,
            detail="No captains assigned to this draft session. Assign captains before starting the draft."
        )

    # 3. Обновляем статус и время в БД
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(seconds=draft_session.pick_time_seconds)
    
    draft_session.status = "in_progress"
    draft_session.started_at = now
    draft_session.current_pick_deadline = deadline

    # 3. Устанавливаем таймер в Redis
    # Ключ будет выглядеть как "draft:1:deadline"
    # EX=... устанавливает время жизни ключа (Time To Live)
    # Это гарантирует, что даже если что-то сломается, ключ исчезнет из Redis
    deadline_key = f"draft:{session_id}:deadline"
    await redis_client.set(deadline_key, deadline.isoformat(), ex=draft_session.pick_time_seconds + 10)

    # 4. Публикуем событие в Redis-канал, чтобы WebSocket его услышал
    # Это как отправить сообщение в общий чат, на который подписаны все WS-серверы
    channel = f"draft:{session_id}"
    message = json.dumps({
        "type": "draft_started",
        "data": {
            "session_id": session_id,
            "start_time": now.isoformat(),
            "first_pick_deadline": deadline.isoformat(),
            "first_captain_id": draft_session.pick_order[0]
        }
    })
    await redis_client.publish(channel, message)
    
    await db.commit()
    return draft_session

async def make_pick(
    db: AsyncSession,
    redis_client: redis.Redis,
    session_id: int,
    pick_data: DraftPickRequest,
    current_user_id: int,
    is_admin: bool = False
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[make_pick] START: session_id={session_id}, current_user_id={current_user_id}, is_admin={is_admin}, pick={pick_data}")

    # --- ШАГ 1: Блокировка и валидация ---

    # Загружаем сессию драфта с блокировкой строки.
    # Никакой другой процесс не сможет изменить эту строку, пока наша транзакция не завершится.
    result = await db.execute(
        select(DraftSession).filter(DraftSession.id == session_id).with_for_update()
    )
    draft_session = result.scalars().first()

    if not draft_session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    if draft_session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Draft is not in progress")

    # Проверяем, чей сейчас ход (админу разрешено в любой ход)
    current_picker_id = draft_session.pick_order[draft_session.current_pick_index]
    if not is_admin and current_picker_id != current_user_id:
        raise HTTPException(status_code=403, detail="It's not your turn to pick")

    # Проверяем, не закончился ли драфт
    total_picks = len(draft_session.pick_order)
    if draft_session.current_pick_index >= total_picks:
        raise HTTPException(status_code=400, detail="Draft has already ended")

    # Загружаем всех уже выбранных игроков
    picked_users_res = await db.execute(select(DraftPick.picked_user_id).filter(DraftPick.draft_session_id == session_id))
    picked_user_ids = {row[0] for row in picked_users_res}

    # Проверяем, не выбран ли этот игрок уже
    if pick_data.picked_user_id in picked_user_ids:
        raise HTTPException(status_code=400, detail="This player has already been picked")
        
    # Проверяем, не является ли игрок капитаном
    captains_res = await db.execute(select(DraftCaptain.user_id).filter(DraftCaptain.draft_session_id == session_id))
    captain_ids = {row[0] for row in captains_res}
    if pick_data.picked_user_id in captain_ids:
        raise HTTPException(status_code=400, detail="Cannot pick a captain")

    # --- ШАГ 2: Запись в БД ---

    # Находим, к какой команде относится пик.
    # ВАЖНО: используем current_picker_id (чей ход), а НЕ current_user_id.
    # Для админа current_user_id != current_picker_id, но пик делается от имени капитана.
    captain_res = await db.execute(select(DraftCaptain).filter(
        DraftCaptain.draft_session_id == session_id,
        DraftCaptain.user_id == current_picker_id
    ))
    captain = captain_res.scalars().first()
    if not captain:
        # Добавляем debug-информацию для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            f"[make_pick] Captain not found! session_id={session_id}, "
            f"current_picker_id={current_picker_id}, current_user_id={current_user_id}, "
            f"is_admin={is_admin}, pick_order={draft_session.pick_order}, "
            f"current_pick_index={draft_session.current_pick_index}"
        )
        raise HTTPException(
            status_code=404,
            detail=f"Picking captain not found: user_id={current_picker_id} (turn owner). Admin={current_user_id}. Pick order has {len(draft_session.pick_order)} entries."
        )

    # Создаем запись о пике
    new_pick = DraftPick(
        draft_session_id=session_id,
        captain_id=captain.id,
        picked_user_id=pick_data.picked_user_id,
        pick_number=draft_session.current_pick_index + 1,
        round_number=(draft_session.current_pick_index // len(captain_ids)) + 1,
        assigned_role=pick_data.assigned_role
    )
    db.add(new_pick)
    
    # --- ШАГ 3: Обновление состояния драфта ---
    
    draft_session.current_pick_index += 1

    if draft_session.current_pick_index >= total_picks:
        draft_session.status = "completed"
        draft_session.completed_at = datetime.now(timezone.utc)

        # Автоматически создаём команды и коммитим всё в одной транзакции
        await complete_draft_session(db, redis_client, session_id)
        # complete_draft_session уже сделал commit + refresh
        # Перезагружаем new_pick чтобы вернуть актуальный объект
        await db.refresh(new_pick)
    else:
        new_deadline = datetime.now(timezone.utc) + timedelta(seconds=draft_session.pick_time_seconds)
        draft_session.current_pick_deadline = new_deadline
        deadline_key = f"draft:{session_id}:deadline"
        await redis_client.set(deadline_key, new_deadline.isoformat(), ex=draft_session.pick_time_seconds + 10)

    await db.commit()
    await db.refresh(new_pick)
    
    # --- ШАГ 4: Публикация события ---
    
    picked_user_res = await db.execute(select(User.username).filter(User.id == new_pick.picked_user_id))
    picked_user_name = picked_user_res.scalars().first()

    next_captain_id = None
    if draft_session.status == 'in_progress':
        next_captain_id = draft_session.pick_order[draft_session.current_pick_index]

    channel = f"draft:{session_id}"
    message = json.dumps({
        "type": "pick_made",
        "data": {
            "pick_number": new_pick.pick_number,
            "round_number": new_pick.round_number,
            "captain_id": captain.user_id,
            "team_id": captain.id,
            "picked_user_id": new_pick.picked_user_id,
            "picked_user_name": picked_user_name or "Unknown",
            "assigned_role": new_pick.assigned_role,
            "next_captain_id": next_captain_id,
        }
    })
    await redis_client.publish(channel, message)
    
    return new_pick

async def get_draft_state(db: AsyncSession, session_id: int):
    # 1. Загружаем сессию
    res = await db.execute(select(DraftSession).filter(DraftSession.id == session_id))
    session = res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")

    # 2. Загружаем капитанов и их юзеров
    CaptainUser = aliased(User)
    captains_res = await db.execute(
        select(DraftCaptain, CaptainUser.username)
        .join(CaptainUser, DraftCaptain.user_id == CaptainUser.id)
        .filter(DraftCaptain.draft_session_id == session_id)
        .order_by(DraftCaptain.pick_position)
    )
    captains = [
        DraftStateCaptain(
            id=cap.id, user_id=cap.user_id, username=username,
            team_name=cap.team_name, pick_position=cap.pick_position
        ) for cap, username in captains_res.all()
    ]
    captain_user_ids = {c.user_id for c in captains}

    # 3. Загружаем сделанные пики
    PickedUser = aliased(User)
    picks_res = await db.execute(
        select(DraftPick, PickedUser.username, DraftCaptain.team_name)
        .join(PickedUser, DraftPick.picked_user_id == PickedUser.id)
        .join(DraftCaptain, DraftPick.captain_id == DraftCaptain.id)
        .filter(DraftPick.draft_session_id == session_id)
        .order_by(DraftPick.pick_number)
    )
    picks = [
        DraftStatePick(
            pick_number=p.pick_number, round_number=p.round_number, captain_id=p.captain_id,
            team_name=team_name, picked_user_id=p.picked_user_id, picked_user_name=username,
            assigned_role=p.assigned_role
        ) for p, username, team_name in picks_res.all()
    ]
    picked_user_ids = {p.picked_user_id for p in picks}

    # 4. Загружаем ПУЛ игроков
    PlayerUser = aliased(User)
    pool_res = await db.execute(
        select(TournamentParticipant, PlayerUser.username)
        .join(PlayerUser, TournamentParticipant.user_id == PlayerUser.id)
        .filter(
            TournamentParticipant.tournament_id == session.tournament_id,
            TournamentParticipant.status == 'registered',
            ~TournamentParticipant.user_id.in_(captain_user_ids | picked_user_ids)
        )
    )
    player_pool = []
    for participant, username in pool_res.all():
        app_data = json.loads(participant.application_data or '{}')
        player_pool.append(DraftStatePlayer(
            user_id=participant.user_id,
            username=username,
            primary_role=app_data.get('primary_role', 'flex'),
            secondary_role=app_data.get('secondary_role', 'flex'),
            rating_approved=app_data.get('rating_approved', 'Unranked')
        ))

    # 5. Собираем всё вместе
    return DraftStateResponse(
        session_id=session.id,
        status=session.status,
        pick_time_seconds=session.pick_time_seconds,
        current_pick_index=session.current_pick_index,
        current_pick_deadline=session.current_pick_deadline,
        pick_order=session.pick_order,
        role_slots=session.role_slots,
        captains=captains,
        picks=picks,
        player_pool=player_pool
    )


async def complete_draft_session(
    db: AsyncSession,
    redis_client: redis.Redis,
    session_id: int
) -> list[Team]:
    """
    Завершает драфт: создаёт Teams из DraftPick, обновляет статусы.

    Логика:
    1. Находит DraftSession и загружает все picks + captains
    2. Валидация: статус должен быть in_progress или completed
       Все пики должны быть сделаны
    3. Группирует picks по captain_id
    4. Для каждого капитана создаёт Team
    5. Обновляет DraftPick.team_id для каждого пика
    6. Обновляет TournamentParticipant.team_id для каждого игрока
    7. Обновляет статус турнира на "upcoming" (если был "draft")
    8. Публикует WS-событие draft_completed
    9. await db.commit()

    Args:
        db: сессия БД
        redis_client: Redis клиент
        session_id: ID сессии драфта

    Returns:
        Список созданных команд

    Raises:
        HTTPException 404 — сессия не найдена
        HTTPException 400 — не все пики сделаны
        HTTPException 409 — драфт ещё не начат или уже завершён
    """
    # 1. Загружаем сессию с капитанами и пиками
    result = await db.execute(
        select(DraftSession)
        .options(
            joinedload(DraftSession.captains),
            joinedload(DraftSession.picks)
        )
        .filter(DraftSession.id == session_id)
    )
    draft_session = result.unique().scalars().first()

    if not draft_session:
        raise HTTPException(status_code=404, detail="Draft session not found")

    # 2. Валидация
    # Разрешаем завершать драфт если он in_progress или только что completed (авто-вызов из make_pick)
    if draft_session.status not in ("in_progress", "completed"):
        raise HTTPException(
            status_code=409,
            detail=f"Draft cannot be completed in '{draft_session.status}' status"
        )

    # Проверяем что команды ещё не созданы (чтобы не дублировать)
    existing_teams_result = await db.execute(
        select(Team).filter(
            Team.tournament_id == draft_session.tournament_id,
            Team.name.in_([cap.team_name for cap in draft_session.captains])
        )
    )
    existing_teams = existing_teams_result.scalars().all()
    if existing_teams:
        raise HTTPException(
            status_code=409,
            detail="Teams have already been created for this draft"
        )

    total_picks = len(draft_session.pick_order)
    if draft_session.current_pick_index < total_picks:
        raise HTTPException(
            status_code=400,
            detail=f"Draft is not fully completed: {draft_session.current_pick_index}/{total_picks} picks done"
        )

    # 3. Группируем пики по captain_id
    picks_by_captain: dict[int, list[DraftPick]] = defaultdict(list)
    for pick in draft_session.picks:
        picks_by_captain[pick.captain_id].append(pick)

    # Сортируем пики внутри каждой команды по pick_number (порядок драфта)
    for cap_id in picks_by_captain:
        picks_by_captain[cap_id].sort(key=lambda p: p.pick_number)

    # 4. Находим капитанов для маппинга
    captains_map = {cap.id: cap for cap in draft_session.captains}

    # 5. Загружаем Tournament этого драфта
    tournament_result = await db.execute(
        select(Tournament).filter(Tournament.id == draft_session.tournament_id)
    )
    tournament = tournament_result.scalars().first()

    # 6. Создаём команды
    created_teams: list[Team] = []

    for captain_id, picks in picks_by_captain.items():
        captain = captains_map.get(captain_id)
        if not captain:
            raise HTTPException(
                status_code=500,
                detail=f"Captain with id={captain_id} not found in draft session"
            )

        # Определяем капитана команды (первый пикнутый игрок или сам капитан)
        # Капитан команды — это сам captain.user_id
        team_name = captain.team_name

        # Создаём команду
        team = Team(
            tournament_id=draft_session.tournament_id,
            name=team_name,
            captain_user_id=captain.user_id
        )
        db.add(team)
        await db.flush()  # получаем team.id

        # Обновляем DraftPick.team_id для каждого пика
        for pick in picks:
            pick.team_id = team.id

            # Обновляем TournamentParticipant.team_id для игрока
            participant_result = await db.execute(
                select(TournamentParticipant).filter(
                    TournamentParticipant.tournament_id == draft_session.tournament_id,
                    TournamentParticipant.user_id == pick.picked_user_id
                )
            )
            participant = participant_result.scalars().first()
            if participant:
                participant.team_id = team.id

        # Также добавим запись TournamentParticipant для самого капитана
        captain_participant_result = await db.execute(
            select(TournamentParticipant).filter(
                TournamentParticipant.tournament_id == draft_session.tournament_id,
                TournamentParticipant.user_id == captain.user_id
            )
        )
        captain_participant = captain_participant_result.scalars().first()
        if captain_participant:
            captain_participant.team_id = team.id

        created_teams.append(team)

    # 7. Обновляем статус драфта (если ещё не completed)
    if draft_session.status != "completed":
        draft_session.status = "completed"
    draft_session.completed_at = datetime.now(timezone.utc)

    # 8. Обновляем статус турнира (если он ещё в статусе "draft")
    if tournament and tournament.status == "draft":
        tournament.status = "upcoming"

    # 9. Очищаем deadline из Redis
    deadline_key = f"draft:{session_id}:deadline"
    try:
        await redis_client.delete(deadline_key)
    except Exception:
        pass  # не критично если ключа нет

    # 10. Публикуем WS-событие draft_completed
    channel = f"draft:{session_id}"
    message = json.dumps({
        "type": "draft_completed",
        "data": {
            "session_id": session_id,
            "teams": [
                {
                    "team_id": team.id,
                    "team_name": team.name,
                    "captain_user_id": team.captain_user_id
                }
                for team in created_teams
            ]
        }
    })
    await redis_client.publish(channel, message)

    # 11. Коммитим всё
    await db.commit()

    # Рефрешим команды чтобы все связи были загружены
    for team in created_teams:
        await db.refresh(team)

    return created_teams