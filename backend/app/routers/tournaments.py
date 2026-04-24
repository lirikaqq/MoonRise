import logging
import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func, exists, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.tournament import Tournament, TournamentParticipant
from app.models.match import Team, Encounter
from app.models.user import User, BattleTag
from app.schemas.participant import ParticipantCore, ParticipantResponse, normalize_participant_data

from app.core.security import decode_access_token, get_current_admin
from app.core.html_sanitizer import sanitize_html
from app.constants import VALID_TOURNAMENT_STATUSES

from app.schemas.tournament import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentShortResponse,
    ApplicationCreateMix,
    ApplicationCreateDraft,
    ApplicationResponse,
    ApplicationApprove,
    ApplicationReject,
    BracketResponse,
    AddParticipantRequest,
    ReplacePlayerRequest,
    ReplacementResponse,
    TeamWithHistoryResponse,
)
from app.schemas.participant import ParticipantCore, normalize_participant_data

from app.services.tournament_service import (
    TournamentService, 
    TeamConfigImmutableError
)


logger = logging.getLogger(__name__)   


router = APIRouter(tags=["tournaments"])


# ============================
# HELPERS для аутентификации
# ============================

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Возвращает юзера если токен валидный, иначе None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            return None
        
        result = await db.execute(
            select(User).where(User.id == int(payload["sub"]))
        )
        return result.scalar_one_or_none()
    except (ValueError, IndexError, AttributeError):
        return None


async def get_current_user_required(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Возвращает юзера или кидает 401."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(
            select(User).where(User.id == int(payload["sub"]))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_required(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Возвращает юзера если он админ, иначе 403."""
    current_user = await get_current_user_required(request, db)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# ============================
# GET /tournaments/
# ============================

@router.get("/", response_model=List[TournamentResponse])
async def get_tournaments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех турниров."""
    result = await db.execute(
        select(Tournament)
        .options(selectinload(Tournament.draft_session))   # ← Добавили это
        .offset(skip)
        .limit(limit)
        .order_by(Tournament.start_date.desc())
    )
    return result.scalars().all()

# ============================
# PRIVATE HELPERS
# ============================

async def _get_tournament_or_404(tournament_id: int, db: AsyncSession) -> Tournament:
    """Простая версия без глубоких загрузок (для отладки)."""
    result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = result.scalar_one_or_none()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    return tournament


# ============================
# GET /tournaments/{id}
# ============================

@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить подробно турнир по ID."""
    result = await db.execute(
        select(Tournament)
        .options(
            selectinload(Tournament.draft_session),
            selectinload(Tournament.teams),
            selectinload(Tournament.stages),
        )
        .where(Tournament.id == tournament_id)
    )
    tournament = result.scalar_one_or_none()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return tournament

# ============================
# GET /users/search
# ============================

@router.get("/users/search")
async def search_users(
    q: str = "",
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Поиск пользователей для админки."""
    if not q or len(q.strip()) < 2:
        return {"users": []}

    query = f"%{q.strip()}%"

    result = await db.execute(
        select(User)
        .where(
            or_(
                User.username.ilike(query),
                User.display_name.ilike(query) if hasattr(User, 'display_name') else False
            )
        )
        .limit(10)
        .order_by(User.username.asc())
    )

    users = result.scalars().all()

    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name or user.username,
                "discord_tag": user.username,           # ← Изменено здесь
            }
            for user in users
        ]
    }

# ============================
# GET /tournaments/users/search
# ============================

@router.get("/users/search")
async def search_users(
    q: str = "",
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Поиск пользователей для админки."""
    if not q or len(q.strip()) < 2:
        return {"users": []}

    try:
        query = f"%{q.strip()}%"

        result = await db.execute(
            select(User)
            .where(
                or_(
                    User.username.ilike(query),
                    User.display_name.ilike(query) if hasattr(User, 'display_name') else False
                )
            )
            .limit(10)
            .order_by(User.username.asc())
        )

        users = result.scalars().all()

        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "display_name": user.display_name or user.username,
                    "discord_tag": getattr(user, 'discord_tag', None),
                }
                for user in users
            ]
        }

    except Exception as e:
        print("=== ERROR IN SEARCH_USERS ===")
        print(type(e).__name__, ":", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during search")
    
# ============================
# POST /tournaments/ (СОЗДАНИЕ)
# ============================

@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament_data: TournamentCreate,           # ← Изменено: используем Pydantic модель
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Создать новый турнир (только админ)."""
    try:
        tournament = await TournamentService.create(db, tournament_data)
        return tournament
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
# ============================
# UPDATE /tournaments/{id}
# ============================

@router.put("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Обновить турнир (только админ)."""
    try:
        tournament = await TournamentService.update(db, tournament_id, tournament_data)
        return tournament
    except TeamConfigImmutableError as e:
        raise e  # Пробрасываем наше кастомное исключение 409
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ============================
# DELETE /tournaments/{id}
# ============================

@router.delete("/{tournament_id}", status_code=status.HTTP_200_OK)
async def delete_tournament(
    tournament_id: int,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Удалить турнир (только админ)."""
    deleted_tournament = await TournamentService.delete_tournament(db, tournament_id)
    
    if not deleted_tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return {
        "message": f"Tournament '{deleted_tournament.title}' and all associated data have been deleted.", 
        "id": tournament_id
    }


# ============================
# PATCH /tournaments/{id}/status
# ============================

@router.patch("/{tournament_id}/status")
async def update_tournament_status(
    tournament_id: int,
    new_status: str,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Обновить статус турнира (только админ)."""
    if new_status not in VALID_TOURNAMENT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {VALID_TOURNAMENT_STATUSES}"
        )

    tournament = await _get_tournament_or_404(tournament_id, db)
    tournament.status = new_status
    await db.commit()
    await db.refresh(tournament)
    return tournament

# ============================
# GET /tournaments/{id}/bracket
# ============================

@router.get("/{tournament_id}/bracket", response_model=BracketResponse)
async def get_tournament_bracket(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить сетку (Bracket) турнира со всеми матчами."""
    
    # Вся сложная логика теперь инкапсулирована в сервисе!
    from app.services.tournament_service import TournamentService
    bracket_data = await TournamentService.get_bracket(db, tournament_id)
    
    return bracket_data

# ============================
# GET /tournaments/{id}/participants
# ============================

@router.get("/{tournament_id}/participants", response_model=ParticipantResponse)
async def get_tournament_participants(
    tournament_id: int,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить участников турнира. С параметром search ищет по Discord или BattleTag."""
    await _get_tournament_or_404(tournament_id, db)

    query = select(TournamentParticipant, User).join(
        User, TournamentParticipant.user_id == User.id
    ).where(TournamentParticipant.tournament_id == tournament_id)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                TournamentParticipant.application_data.ilike(f'%battletag_value%:%{search_term}%'),
                TournamentParticipant.application_data.ilike(f'%discord_tag%:%{search_term}%'),
                User.username.ilike(search_term),
                User.display_name.ilike(search_term)
            )
        )

    result = await db.execute(query.order_by(TournamentParticipant.registered_at.asc()))
    rows = result.all()

    participants = []
    for p, u in rows:
        # Получаем основной BattleTag пользователя (если есть)
        battletag_query = select(BattleTag).where(
            BattleTag.user_id == u.id,
            BattleTag.is_primary == True
        ).limit(1)
        battletag_result = await db.execute(battletag_query)
        battletag_obj = battletag_result.scalar_one_or_none()
        battletag = battletag_obj.tag if battletag_obj else None

        # Нормализуем данные участника
        participant_data = normalize_participant_data(p, u, battletag)
        participants.append(participant_data)

    return {"participants": participants}

# ============================
# GET /tournaments/{tournament_id}/teams
# ============================

@router.get("/{tournament_id}/teams")
async def get_tournament_teams(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить все команды турнира с игроками."""
    await _get_tournament_or_404(tournament_id, db)

    result = await db.execute(
        select(Team)
        .where(Team.tournament_id == tournament_id)
        .options(
            selectinload(Team.tournament_participants)
            .selectinload(TournamentParticipant.user)
        )
    )
    teams = result.scalars().all()

    return {
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "division": getattr(team, 'division', None),   # ← Безопасно
                "players": [
                    {
                        "id": p.id,
                        "user_id": p.user_id,
                        "display_name": p.user.display_name or p.user.username if p.user else "—",
                        "username": p.user.username if p.user else "—",
                        "is_captain": p.is_captain or False,
                        "application_data": json.loads(p.application_data) if isinstance(p.application_data, str) 
                                           else (p.application_data if isinstance(p.application_data, dict) else {})
                    }
                    for p in sorted(team.tournament_participants, key=lambda x: (not x.is_captain, x.id))
                ]
            }
            for team in teams
        ]
    }

# ============================
# GET /tournaments/{id}/my-status
# ============================

@router.get("/{tournament_id}/my-status")
async def get_my_tournament_status(
    tournament_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Получить статус моей заявки на турнир."""
    await _get_tournament_or_404(tournament_id, db)

    if not current_user:
        return {
            "registered": False,
            "status": None,
            "is_allowed": False,
            "application_data": None
        }

    p_result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == current_user.id
        )
    )
    participant = p_result.scalar_one_or_none()

    if not participant:
        return {
            "registered": False,
            "status": None,
            "is_allowed": False,
            "application_data": None
        }

    # Парсим JSON-строку обратно в объект
    app_data = None
    if participant.application_data:
        try:
            app_data = json.loads(participant.application_data)
        except json.JSONDecodeError:
            app_data = {}

    return {
        "registered": True,
        "status": participant.status,
        "is_allowed": participant.is_allowed,
        "application_data": app_data,
        "registered_at": participant.registered_at.isoformat() if participant.registered_at else None,
        "updated_at": participant.updated_at.isoformat() if participant.updated_at else None,
    }


# ============================
# POST /tournaments/{id}/register/mix
# ============================

@router.post("/{tournament_id}/register/mix", status_code=status.HTTP_201_CREATED)
async def register_for_tournament_mix(
    tournament_id: int,
    body: ApplicationCreateMix,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    tournament = await _get_tournament_or_404(tournament_id, db)
    if tournament.format != "mix":
        raise HTTPException(status_code=400, detail="This tournament requires /register/mix endpoint")
    if tournament.status != "registration":
        raise HTTPException(status_code=400, detail="Registration is not open for this tournament")

    await _check_participants_limit(tournament, db)

    now = datetime.now(timezone.utc)
    application_json = json.dumps({
        "primary_role": body.primary_role,
        "secondary_role": body.secondary_role,
        "bio": body.bio,
        "confirmed_friend_request": body.confirmed_friend_request,
        "confirmed_rules": body.confirmed_rules,
        "submitted_at": now.isoformat(),
        "approved_at": None,
        "approved_by": None,
        "rejected_at": None,
        "rejected_reason": None,
    }, ensure_ascii=False)

    # ИЩЕМ, ЕСТЬ ЛИ УЖЕ ЗАЯВКА
    result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == current_user.id
        )
    )
    existing_participant = result.scalar_one_or_none()

    if existing_participant:
        if existing_participant.status != "rejected":
            raise HTTPException(status_code=400, detail="You are already registered for this tournament")
        
        # ЕСЛИ БЫЛА ОТКЛОНЕНА -> ОБНОВЛЯЕМ ЕЁ
        existing_participant.status = "pending"
        existing_participant.application_data = application_json
        existing_participant.updated_at = now
    else:
        # СОЗДАЁМ НОВУЮ
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            user_id=current_user.id,
            status="pending",
            is_allowed=False,
            registered_at=now,
            updated_at=now,
            application_data=application_json
        )
        db.add(participant)
    
    await db.commit()

    return {"message": "Application submitted, waiting for admin approval", "tournament_id": tournament_id, "status": "pending"}


@router.post("/{tournament_id}/register/draft", status_code=status.HTTP_201_CREATED)
async def register_for_tournament_draft(
    tournament_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    try:
        body_bytes = await request.body()
        try:
            body_str = body_bytes.decode('utf-8')
        except UnicodeDecodeError:
            body_str = body_bytes.decode('cp1251')

        body_json = json.loads(body_str)
        body = ApplicationCreateDraft(**body_json)

        tournament = await _get_tournament_or_404(tournament_id, db)
        if tournament.format != "draft":
            raise HTTPException(status_code=400, detail="This tournament requires /register/draft endpoint")
        if tournament.status != "registration":
            raise HTTPException(status_code=400, detail="Registration is not open for this tournament")

        await _check_participants_limit(tournament, db)

        battletag_id, battletag_value = await _resolve_battletag(body=body, user=current_user, db=db)

        now = datetime.now(timezone.utc)
        application_json = json.dumps({
            "primary_role": body.primary_role,
            "secondary_role": body.secondary_role,
            "bio": body.bio,
            "rating_claimed": body.rating_claimed,
            "rating_approved": None,
            "battletag_id": battletag_id,
            "battletag_value": battletag_value,
            "confirmed_friend_request": body.confirmed_friend_request,
            "confirmed_rules": body.confirmed_rules,
            "submitted_at": now.isoformat(),
            "approved_at": None,
            "approved_by": None,
            "rejected_at": None,
            "rejected_reason": None,
        }, ensure_ascii=False)

        # ИЩЕМ СТАРУЮ ЗАЯВКУ
        result = await db.execute(
            select(TournamentParticipant).where(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.user_id == current_user.id
            )
        )
        existing_participant = result.scalar_one_or_none()

        if existing_participant:
            if existing_participant.status != "rejected":
                raise HTTPException(status_code=400, detail="You are already registered for this tournament")
            
            # ВОСКРЕШАЕМ ОТКЛОНЁННУЮ
            existing_participant.status = "pending"
            existing_participant.application_data = application_json
            existing_participant.updated_at = now
        else:
            participant = TournamentParticipant(
                tournament_id=tournament_id,
                user_id=current_user.id,
                status="pending",
                is_allowed=False,
                registered_at=now,
                updated_at=now,
                application_data=application_json
            )
            db.add(participant)
            
        await db.commit()

        return {"message": "Application submitted", "tournament_id": tournament_id, "status": "pending"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
# ============================
# POST /tournaments/{id}/checkin
# ============================

@router.post("/{tournament_id}/checkin")
async def checkin_for_tournament(
    tournament_id: int,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """Check-in на турнир (только одобренные участники)."""
    tournament = await _get_tournament_or_404(tournament_id, db)

    if tournament.status != "checkin":
        raise HTTPException(
            status_code=400,
            detail="Check-in is not open for this tournament"
        )

    p_result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == current_user.id
        )
    )
    participant = p_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=400, detail="Not registered for this tournament")
    
    if not participant.is_allowed:
        raise HTTPException(status_code=403, detail="Your application is not approved yet")

    if participant.checkedin_at:
        raise HTTPException(status_code=400, detail="Already checked in")

    participant.checkedin_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Check-in successful", "tournament_id": tournament_id}


# ============================
# GET /tournaments/{id}/applications (АДМИНКА)
# ============================

@router.get("/{tournament_id}/applications")
async def get_applications(
    tournament_id: int,
    status_filter: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Список всех заявок на турнир (только для админа)."""
    await _get_tournament_or_404(tournament_id, db)

    # ДОБАВЛЕНО: Теперь джоиним таблицу User, чтобы получить никнейм
    query = select(TournamentParticipant, User).join(
        User, TournamentParticipant.user_id == User.id
    ).where(
        TournamentParticipant.tournament_id == tournament_id
    )

    if status_filter in ("pending", "registered", "rejected"):
        query = query.where(TournamentParticipant.status == status_filter)

    result = await db.execute(query.order_by(TournamentParticipant.registered_at.asc()))
    rows = result.all()

    applications = []
    for p, u in rows:
        app_data = None
        if p.application_data:
            try:
                app_data = json.loads(p.application_data)
            except:
                app_data = {}

        applications.append({
            "id": p.id,
            "user_id": p.user_id,
            "user_username": u.username,               # ← ДОБАВЛЕН НИК
            "user_display_name": u.display_name,       # ← ДОБАВЛЕН НИК
            "status": p.status,
            "is_allowed": p.is_allowed,
            "application_data": app_data,
            "registered_at": p.registered_at.isoformat() if p.registered_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    return {"applications": applications, "total": len(applications)}

# ============================
# POST /tournaments/{id}/applications/{user_id}/approve (АДМИНКА)
# ============================

@router.post("/{tournament_id}/applications/{user_id}/approve")
async def approve_application(
    tournament_id: int,
    user_id: int,
    body: ApplicationApprove,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Одобрить заявку (только для админа)."""

    # 1. Проверяем что турнир существует
    await _get_tournament_or_404(tournament_id, db)

    # 2. Находим заявку
    p_result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        )
    )
    participant = p_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Application not found")

    if participant.status == "registered":
        raise HTTPException(status_code=400, detail="Application already approved")

    # 3. Обновляем application_data
    now = datetime.now(timezone.utc)

    # Парсим текущие данные
    if participant.application_data:
        try:
            app_data = json.loads(participant.application_data)
        except json.JSONDecodeError:
            app_data = {}
    else:
        app_data = {}

    # Обновляем данные
    app_data.update({
        "approved_at": now.isoformat(),
        "approved_by": current_admin.id,
        "rejected_at": None,
        "rejected_reason": None,
    })
    
    # Для draft-турниров сохраняем одобренный рейтинг
    if body.rating_approved:
        app_data["rating_approved"] = body.rating_approved

    # Сохраняем обратно как JSON-строку
    participant.application_data = json.dumps(app_data, ensure_ascii=False)

    # 4. Обновляем запись
    participant.status = "registered"
    participant.is_allowed = True
    participant.updated_at = now

    await db.commit()

    return {"message": "Application approved", "user_id": user_id}


# ============================
# POST /tournaments/{id}/applications/{user_id}/reject (АДМИНКА)
# ============================

@router.post("/{tournament_id}/applications/{user_id}/reject")
async def reject_application(
    tournament_id: int,
    user_id: int,
    body: ApplicationReject,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Отклонить заявку (только для админа)."""

    await _get_tournament_or_404(tournament_id, db)

    p_result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        )
    )
    participant = p_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Application not found")

    if participant.status == "rejected":
        raise HTTPException(status_code=400, detail="Application already rejected")

    # Обновляем application_data
    now = datetime.now(timezone.utc)
    
    if participant.application_data:
        try:
            app_data = json.loads(participant.application_data)
        except json.JSONDecodeError:
            app_data = {}
    else:
        app_data = {}

    app_data.update({
        "rejected_at": now.isoformat(),
        "rejected_reason": body.reason,
        "approved_at": None,
        "approved_by": None,
    })

    participant.application_data = json.dumps(app_data, ensure_ascii=False)
    participant.status = "rejected"
    participant.is_allowed = False
    participant.updated_at = now

    await db.commit()

    return {"message": "Application rejected", "user_id": user_id}

# ============================
# POST /tournaments/{id}/add-participant (АДМИН)
# ============================

@router.post("/{tournament_id}/add-participant")
async def add_participant_manually(
    tournament_id: int,
    data: AddParticipantRequest,                    # ← Используем Pydantic модель
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Админ вручную добавляет участника (существующего или нового)."""
    tournament = await _get_tournament_or_404(tournament_id, db)

    # Ищем пользователя
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            username=data.username,
            display_name=data.discord_tag or data.username,
            role="user",
            is_ghost=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        await db.flush()

    # Проверка на дубликат
    existing = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already registered for this tournament")

    app_data = {
        "primary_role": data.primary_role,
        "secondary_role": data.secondary_role,
        "battletag_value": data.battletag_value,
        "division": data.division,
        "bio": data.bio,
        "added_by_admin": True,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }

    participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_id=user.id,
        status="registered",
        is_allowed=True,
        is_captain=data.is_captain,
        application_data=json.dumps(app_data, ensure_ascii=False),
        registered_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(participant)
    await db.commit()
    await db.refresh(participant)

    return {"success": True, "message": "Участник успешно добавлен", "participant_id": participant.id}

# ============================
# GET /tournaments/{id}/free-players
# ============================

@router.get("/{tournament_id}/free-players")
async def get_free_players(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Возвращает только тех зарегистрированных игроков, которые реально НЕ состоят ни в одной команде."""
    await _get_tournament_or_404(tournament_id, db)

    result = await db.execute(
        select(TournamentParticipant, User)
        .join(User, TournamentParticipant.user_id == User.id)
        .where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.status == "registered",
            # Исключаем всех, у кого уже есть запись с заполненным team_id
            ~exists().where(
                (TournamentParticipant.user_id == TournamentParticipant.user_id) &
                (TournamentParticipant.tournament_id == tournament_id) &
                (TournamentParticipant.team_id.isnot(None))
            )
        )
        .options(selectinload(TournamentParticipant.user))
        .order_by(TournamentParticipant.registered_at.asc())
    )

    rows = result.all()
    free_players = []

    for participant, user in rows:
        app_data = json.loads(participant.application_data) if participant.application_data else {}
        
        free_players.append({
            "user_id": user.id,
            "user_display_name": user.display_name or user.username,
            "user_username": user.username,
            "application_data": app_data,
            "is_captain": participant.is_captain,
        })

    return {"free_players": free_players}

# ============================
# PLAYER REPLACEMENT SYSTEM (только для админа)
# ============================

@router.post("/{tournament_id}/teams/{team_id}/replace", status_code=status.HTTP_201_CREATED)
async def replace_player_in_team(
    tournament_id: int,
    team_id: int,
    body: ReplacePlayerRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Заменить игрока в команде (только админ)."""
    try:
        result = await TournamentService.replace_player(
            db=db,
            tournament_id=tournament_id,
            team_id=team_id,
            old_participant_id=body.old_participant_id,
            new_participant_id=body.new_participant_id,
            replaced_by_user_id=current_admin.id,
            reason=body.reason,
        )
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in replace_player: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{tournament_id}/teams/{team_id}/replace/{replacement_id}/undo")
async def undo_player_replacement(
    tournament_id: int,
    team_id: int,
    replacement_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Откатить замену (только админ)."""
    try:
        result = await TournamentService.undo_replace(
            db=db,
            replacement_id=replacement_id,
            undone_by_user_id=current_admin.id
        )
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in undo_replace: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tournament_id}/teams/{team_id}/history")
async def get_team_replacement_history(
    tournament_id: int,
    team_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Получить историю замен в команде (для админки)."""
    try:
        await TournamentService.get_by_id(db, tournament_id)  # проверка существования турнира
        return await TournamentService.get_team_with_history(db, team_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_team_replacement_history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



# ============================
# PRIVATE HELPERS
# ============================

async def _get_tournament_or_404(tournament_id: int, db: AsyncSession) -> Tournament:
    """Возвращает турнир или кидает 404."""
    result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


async def _check_participants_limit(tournament: Tournament, db: AsyncSession) -> None:
    """Проверяет лимит участников."""
    if not tournament.max_participants:
        return

    count_result = await db.execute(
        select(func.count(TournamentParticipant.id)).where(
            TournamentParticipant.tournament_id == tournament.id,
            # Считаем только active заявки (pending + registered)
            TournamentParticipant.status.in_(["pending", "registered"])
        )
    )
    count = count_result.scalar()

    if count >= tournament.max_participants:
        raise HTTPException(status_code=400, detail="Tournament is full")


async def _resolve_battletag(
    body: ApplicationCreateDraft,
    user: User,
    db: AsyncSession
) -> tuple:
    """
    Возвращает (battletag_id, battletag_value).
    
    Если передан battletag_id → проверяем что он принадлежит юзеру.
    Если передан new_battletag → создаём новый BattleTag в БД.
    """
    if body.battletag_id:
        # Проверяем что этот battletag принадлежит текущему юзеру
        bt_result = await db.execute(
            select(BattleTag).where(
                BattleTag.id == body.battletag_id,
                BattleTag.user_id == user.id
            )
        )
        battletag = bt_result.scalar_one_or_none()

        if not battletag:
            raise HTTPException(
                status_code=400,
                detail="BattleTag not found or doesn't belong to you"
            )

        return battletag.id, battletag.tag

    else:
        # Создаём новый BattleTag
        # Проверяем что такой tag уже не добавлен этим юзером
        existing_bt = await db.execute(
            select(BattleTag).where(
                BattleTag.user_id == user.id,
                BattleTag.tag == body.new_battletag
            )
        )
        if existing_bt.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="This BattleTag is already in your profile"
            )

        new_bt = BattleTag(
            user_id=user.id,
            tag=body.new_battletag,
            is_primary=False,
        )
        db.add(new_bt)
        await db.flush()  # flush чтобы получить id до commit

        return new_bt.id, new_bt.tag
    

    # ============================
# GOOGLE SHEETS INTEGRATION
# ============================

@router.put("/{tournament_id}/sheet-id")
async def set_google_sheet_id(
    tournament_id: int,
    body: dict,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Сохранить ID Google таблицы для турнира."""
    result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = result.scalar_one_or_none()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    tournament.google_sheet_id = body.get("sheet_id")
    db.add(tournament)
    await db.commit()
    await db.refresh(tournament)
    
    return {"success": True, "sheet_id": tournament.google_sheet_id}


@router.post("/{tournament_id}/export-to-sheets")
async def export_to_google_sheets(
    tournament_id: int,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Экспорт участников турнира в Google Sheets."""
    from app.services.sheets_service import SheetsService
    
    result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = result.scalar_one_or_none()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if not tournament.google_sheet_id:
        raise HTTPException(status_code=400, detail="Google sheet ID not set")

    participants_result = await db.execute(
        select(TournamentParticipant, User).join(
            User, TournamentParticipant.user_id == User.id
        ).where(TournamentParticipant.tournament_id == tournament_id)
    )
    participants_data = []
    for participant, user in participants_result.all():
        participants_data.append({
            "discord": user.username or "",
            "battle_tag": user.battle_tag or "",
            "alt_battle_tags": "",
            "primary_role": "",
            "secondary_role": "",
            "wants_captain": participant.is_captain,
            "notes": "",
            "division": user.division or "",
            "approved": participant.is_allowed,
            "banned": participant.status == "banned",
            "checked_in": participant.checkedin_at is not None,
        })

    sheets_service = SheetsService()
    result = await sheets_service.export_participants(
        tournament.google_sheet_id,
        tournament.title,
        participants_data
    )

    return result



# ============================
# CAPTAIN MANAGEMENT (CAPTAIN ENDPOINTS)
# ============================

@router.post("/participants/{participant_id}/promote")
async def promote_to_captain(
    participant_id: int,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Назначить участника капитаном (только админ)."""
    result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    if participant.is_allowed:
        # Проверяем что заявка одобрена перед назначением капитана
        pass
    else:
        raise HTTPException(
            status_code=400, 
            detail="Participant must be approved before promoting to captain"
        )
    
    # Снимаем статус капитана со всех остальных участников этого турнира
    await db.execute(
        update(TournamentParticipant)
        .where(
            TournamentParticipant.tournament_id == participant.tournament_id,
            TournamentParticipant.is_captain == True
        )
        .values(is_captain=False)
    )
    
    # Назначаем нового капитана
    participant.is_captain = True
    participant.updated_at = datetime.now(timezone.utc)
    
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    
    return {
        "success": True,
        "message": f"{participant.user.username} promoted to captain",
        "tournament_id": participant.tournament_id,
        "participant_id": participant_id
    }


@router.post("/participants/{participant_id}/demote")
async def demote_from_captain(
    participant_id: int,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Снять статус капитана с участника (только админ)."""
    result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    if not participant.is_captain:
        raise HTTPException(
            status_code=400, 
            detail="This participant is not a captain"
        )
    
    participant.is_captain = False
    participant.updated_at = datetime.now(timezone.utc)
    
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    
    return {
        "success": True,
        "message": f"{participant.user.username} demoted from captain",
        "tournament_id": participant.tournament_id,
        "participant_id": participant_id
    }


@router.get("/{tournament_id}/captains")
async def get_tournament_captains(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить список капитанов турнира."""
    tournament = await _get_tournament_or_404(tournament_id, db)
    
    result = await db.execute(
        select(TournamentParticipant, User)
        .join(User, TournamentParticipant.user_id == User.id)
        .where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.is_captain == True,
            TournamentParticipant.status.in_(["pending", "registered"])
        )
        .order_by(TournamentParticipant.registered_at.asc())
    )
    captains = result.all()
    
    captains_list = []
    for p, u in captains:
        app_data = {}
        if p.application_data:
            try:
                app_data = json.loads(p.application_data)
            except:
                pass
        
        captains_list.append({
            "id": p.id,
            "user_id": u.id,
            "username": u.username,
            "display_name": u.display_name or u.username,
            "battle_tag": app_data.get("battletag_value"),
            "primary_role": app_data.get("primary_role"),
            "secondary_role": app_data.get("secondary_role"),
            "team_name": None,  # Заполняется после драфта
            "status": p.status,
        })
    
    return {
        "tournament_id": tournament_id,
        "tournament_title": tournament.title,
        "captains_count": len(captains_list),
        "captains": captains_list
    }


# ============================
# BULK ACTIONS (МАССОВЫЕ ДЕЙСТВИЯ)
# ============================

from pydantic import BaseModel
from typing import List

class BulkApproveReject(BaseModel):
    user_ids: List[int]

@router.post("/{tournament_id}/applications/approve-bulk")
async def approve_applications_bulk(
    tournament_id: int,
    body: BulkApproveReject,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Массовое одобрение заявок (только админ)."""
    tournament = await _get_tournament_or_404(tournament_id, db)
    now = datetime.now(timezone.utc)
    
    approved_count = 0
    for user_id in body.user_ids:
        result = await db.execute(
            select(TournamentParticipant).where(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.user_id == user_id
            )
        )
        participant = result.scalar_one_or_none()
        
        if participant and participant.status != "registered":
            # Обновляем заявку
            app_data = {}
            if participant.application_data:
                try:
                    app_data = json.loads(participant.application_data)
                except:
                    pass
            
            app_data.update({
                "approved_at": now.isoformat(),
                "approved_by": current_admin.id,
            })
            
            participant.application_data = json.dumps(app_data, ensure_ascii=False)
            participant.status = "registered"
            participant.is_allowed = True
            participant.updated_at = now
            
            db.add(participant)
            approved_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "approved_count": approved_count,
        "total_requested": len(body.user_ids)
    }


@router.post("/{tournament_id}/applications/reject-bulk")
async def reject_applications_bulk(
    tournament_id: int,
    body: BulkApproveReject,
    reason: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Массовое отклонение заявок (только админ)."""
    tournament = await _get_tournament_or_404(tournament_id, db)
    now = datetime.now(timezone.utc)
    
    rejected_count = 0
    for user_id in body.user_ids:
        result = await db.execute(
            select(TournamentParticipant).where(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.user_id == user_id
            )
        )
        participant = result.scalar_one_or_none()
        
        if participant and participant.status != "rejected":
            # Обновляем заявку
            app_data = {}
            if participant.application_data:
                try:
                    app_data = json.loads(participant.application_data)
                except:
                    pass
            
            app_data.update({
                "rejected_at": now.isoformat(),
                "rejected_reason": reason or "Rejected by admin",
                "approved_at": None,
                "approved_by": None,
            })
            
            participant.application_data = json.dumps(app_data, ensure_ascii=False)
            participant.status = "rejected"
            participant.is_allowed = False
            participant.updated_at = now
            
            db.add(participant)
            rejected_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "rejected_count": rejected_count,
        "total_requested": len(body.user_ids)
    }


@router.post("/{tournament_id}/teams/{team_id}/replace/{old_participant_id}")
async def replace_player_in_team(
    tournament_id: int,
    team_id: int,
    old_participant_id: int,
    new_user_id: int,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Заменить игрока в команде."""
    # Проверяем существование старого участника
    old = await db.get(TournamentParticipant, old_participant_id)
    if not old or old.tournament_id != tournament_id or old.team_id != team_id:
        raise HTTPException(status_code=404, detail="Old participant not found in team")

    # Проверяем нового пользователя
    new_user = await db.get(User, new_user_id)
    if not new_user:
        raise HTTPException(status_code=404, detail="New user not found")

    # Создаём нового участника
    new_participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_id=new_user_id,
        team_id=team_id,
        status="registered",
        is_allowed=True,
        is_captain=False,
        application_data=old.application_data,  # копируем данные
        registered_at=datetime.now(timezone.utc),
        replaced_by=old.id,
        replaced_at=datetime.now(timezone.utc)
    )

    db.add(new_participant)
    await db.commit()
    await db.refresh(new_participant)

    return {
        "success": True,
        "message": "Игрок успешно заменён",
        "old_participant_id": old.id,
        "new_participant_id": new_participant.id
    }