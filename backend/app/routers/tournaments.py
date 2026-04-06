# backend/app/routers/tournaments.py

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timezone

# Models
from app.database import get_db
from app.models.tournament import Tournament, TournamentParticipant
from app.models.user import User, BattleTag

# Core
from app.core.security import decode_access_token

# Constants
from app.constants import VALID_TOURNAMENT_STATUSES

# Schemas
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
)

from app.schemas.tournament import BracketResponse
from app.services.tournament_service import TournamentService 

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
        .offset(skip)
        .limit(limit)
        .order_by(Tournament.start_date.desc())
    )
    return result.scalars().all()


# ============================
# GET /tournaments/{id}
# ============================

@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить подробно турнир по ID."""
    tournament = await _get_tournament_or_404(tournament_id, db)
    return tournament


# ============================
# POST /tournaments/ (СОЗДАНИЕ)
# ============================

@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    request: Request,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Создать новый турнир (только админ)."""
    try:
        body = await request.json()
        
        # Валидируем формат
        if body.get("format") not in ("mix", "draft"):
            raise HTTPException(status_code=400, detail="Format must be 'mix' or 'draft'")
        
        tournament = Tournament(
            title=body["title"],
            format=body["format"],
            description=body.get("description"),
            start_date=datetime.fromisoformat(body["start_date"].replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(body["end_date"].replace('Z', '+00:00')),
            status=body.get("status", "upcoming"),
            max_participants=body.get("max_participants", 100)
        )

        db.add(tournament)
        await db.commit()
        await db.refresh(tournament)
        return tournament

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


# ============================
# PUT /tournaments/{id}
# ============================

@router.put("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    current_admin: User = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Обновить турнир (только админ)."""
    tournament = await _get_tournament_or_404(tournament_id, db)

    update_data = tournament_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tournament, field, value)

    await db.commit()
    await db.refresh(tournament)
    return tournament


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

@router.get("/{tournament_id}/participants")
async def get_tournament_participants(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить список одобренных участников турнира (публичный)."""
    await _get_tournament_or_404(tournament_id, db)

    result = await db.execute(
        select(TournamentParticipant, User)
        .join(User, TournamentParticipant.user_id == User.id)
        .where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.is_allowed == True
        )
        .order_by(TournamentParticipant.registered_at.asc())
    )
    rows = result.all()

    participants = []
    for participant, user in rows:
        # Тянем роли и батлтег именно из ЗАЯВКИ, а не из профиля
        app_data = {}
        if participant.application_data:
            try:
                app_data = json.loads(participant.application_data)
            except:
                pass

        participants.append({
            "id": user.id,
            "battle_tag": app_data.get("battletag_value") or user.username,
            "display_name": user.display_name or user.username,
            "avatar_url": user.avatar_url,
            "primary_role": app_data.get("primary_role"),
            "secondary_role": app_data.get("secondary_role"),
            "bio": app_data.get("bio"),
            "status": participant.status,
            "is_allowed": participant.is_allowed,
            "registered_at": participant.registered_at.isoformat() if participant.registered_at else None,
        })

    return participants


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