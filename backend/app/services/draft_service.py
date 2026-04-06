# app/services/draft_service.py
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.draft import DraftSession, DraftCaptain
from app.models.tournament import Tournament, TournamentParticipant
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

    # 2. Проверяем капитанов
    captains_res = await db.execute(
        select(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id.in_(setup_data.captain_user_ids),
            TournamentParticipant.status == "registered"
        )
    )
    captains_query = captains_res.scalars().all()
    
    if len(captains_query) != len(setup_data.captain_user_ids):
        raise HTTPException(status_code=400, detail="Some captains are not approved participants")

    # 3. ГЕНЕРАЦИЯ ЗМЕЙКИ (логика не меняется)
    pick_order = []
    for round_num in range(1, setup_data.team_size + 1):
        if round_num % 2 != 0:
            pick_order.extend(setup_data.captain_user_ids)
        else:
            pick_order.extend(reversed(setup_data.captain_user_ids))

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
    await db.flush() # Используем await db.flush()

    # 5. Создаем капитанов
    for position, cap_user_id in enumerate(setup_data.captain_user_ids, start=1):
        team_name = setup_data.team_names[cap_user_id]
        cap_participant = next(p for p in captains_query if p.user_id == cap_user_id)
        
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
    db.add(tournament) # Добавляем измененный объект в сессию
    
    await db.commit() # Используем await db.commit()
    return draft_session

async def start_draft(db: AsyncSession, redis_client: redis.Redis, session_id: int):
    # 1. Находим сессию драфта
    result = await db.execute(select(DraftSession).filter(DraftSession.id == session_id))
    draft_session = result.scalars().first()

    if not draft_session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    if draft_session.status != "pending":
        raise HTTPException(status_code=400, detail="Draft can only be started from 'pending' status")

    # 2. Обновляем статус и время в БД
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(seconds=draft_session.pick_time_seconds)
    
    draft_session.status = "in_progress"
    draft_session.started_at = now
    draft_session.current_pick_deadline = deadline
    
    db.add(draft_session)

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
    current_user_id: int
):
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

    # Проверяем, чей сейчас ход
    current_picker_id = draft_session.pick_order[draft_session.current_pick_index]
    if current_picker_id != current_user_id:
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
    
    # Находим, к какой команде относится пик
    captain_res = await db.execute(select(DraftCaptain).filter(
        DraftCaptain.draft_session_id == session_id,
        DraftCaptain.user_id == current_user_id
    ))
    captain = captain_res.scalars().first()
    if not captain:
        # Эта ошибка не должна произойти, если валидация хода прошла, но для надежности
        raise HTTPException(status_code=404, detail="Picking captain not found in this draft session.")

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
    else:
        new_deadline = datetime.now(timezone.utc) + timedelta(seconds=draft_session.pick_time_seconds)
        draft_session.current_pick_deadline = new_deadline
        deadline_key = f"draft:{session_id}:deadline"
        await redis_client.set(deadline_key, new_deadline.isoformat(), ex=draft_session.pick_time_seconds + 10)

    db.add(draft_session)
    await db.commit()
    await db.refresh(new_pick) # Обновляем new_pick, чтобы получить его ID и другие поля из БД
    
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
    print("2. Сессия загружена")

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

    print("3. Капитаны загружены")

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

    print("4. Пики загружены")

    # 4. Загружаем ПУЛ игроков (все одобренные участники минус капитаны и уже выбранные)
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
        print("4. Пики загружены")
        print("5. Пул загружен")
        print("6. Собираем ответ")

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