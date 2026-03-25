from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.services.tournament_service import TournamentService
from app.models.tournament import TournamentParticipant
from app.schemas.tournament import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentShortResponse,
)
from app.core.security import decode_access_token

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def get_user_id_from_token(authorization: str = None) -> int:
    """Достать user_id из Bearer токена."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token required")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload.get("sub"))


@router.get("", response_model=list[TournamentShortResponse])
async def get_tournaments(
    format: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    tournaments = await TournamentService.get_all(
        db, format=format, search=search, skip=skip, limit=limit
    )
    return tournaments


@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    tournament = await TournamentService.get_by_id(db, tournament_id)
    return tournament


@router.post("", response_model=TournamentResponse)
async def create_tournament(
    data: TournamentCreate,
    db: AsyncSession = Depends(get_db)
):
    tournament = await TournamentService.create(db, data)
    return tournament


@router.put("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: int,
    data: TournamentUpdate,
    db: AsyncSession = Depends(get_db)
):
    tournament = await TournamentService.update(db, tournament_id, data)
    return tournament


@router.delete("/{tournament_id}")
async def delete_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await TournamentService.delete(db, tournament_id)
    return result


@router.patch("/{tournament_id}/status", response_model=TournamentResponse)
async def update_tournament_status(
    tournament_id: int,
    status: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    tournament = await TournamentService.update_status(db, tournament_id, status)
    return tournament


@router.post("/{tournament_id}/register")
async def register_for_tournament(
    tournament_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Регистрация на турнир."""
    user_id = get_user_id_from_token(authorization)

    tournament = await TournamentService.get_by_id(db, tournament_id)

    # Проверка статуса
    if tournament.status != "registration":
        raise HTTPException(status_code=400, detail="Registration is not open")

    # Проверка мест
    if tournament.participants_count >= (tournament.max_participants or 999):
        raise HTTPException(status_code=400, detail="Tournament is full")

    # Проверка — уже зарегистрирован?
    result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Already registered for this tournament")

    # Создаём запись участника
    participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_id=user_id,
        status="registered",
        registered_at=datetime.utcnow()
    )
    db.add(participant)

    # Увеличиваем счётчик
    tournament.participants_count += 1
    await db.commit()

    return {
        "message": "Successfully registered",
        "tournament_id": tournament_id,
        "status": "registered"
    }


@router.post("/{tournament_id}/checkin")
async def checkin_tournament(
    tournament_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Чек-ин на турнир."""
    user_id = get_user_id_from_token(authorization)

    tournament = await TournamentService.get_by_id(db, tournament_id)

    if tournament.status != "checkin":
        raise HTTPException(status_code=400, detail="Check-in is not open")

    # Проверка — зарегистрирован?
    result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=400, detail="You are not registered for this tournament")

    # Проверка — уже чекнулся?
    if participant.status == "checkedin":
        raise HTTPException(status_code=400, detail="Already checked in")

    participant.status = "checkedin"
    participant.checkedin_at = datetime.utcnow()
    await db.commit()

    return {
        "message": "Check-in confirmed",
        "tournament_id": tournament_id,
        "status": "checkedin"
    }


@router.get("/{tournament_id}/my-status")
async def get_my_status(
    tournament_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Статус текущего пользователя в турнире."""
    user_id = get_user_id_from_token(authorization)

    result = await db.execute(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        return {"status": None, "registered": False}

    return {
        "status": participant.status,
        "registered": True,
        "registered_at": participant.registered_at,
        "checkedin_at": participant.checkedin_at
    }