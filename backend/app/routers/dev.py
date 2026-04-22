"""
Dev-only endpoints for debugging and testing.
NOT available in production (guarded by ENVIRONMENT check).
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.models.tournament import Tournament, TournamentParticipant
from app.models.draft import DraftSession, DraftPick, DraftCaptain
from app.config import settings

router = APIRouter(prefix="/api/dev", tags=["Dev (debug only)"])


@router.post("/tournaments/{tournament_id}/seed-participants")
async def seed_participants_for_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    [DEV ONLY] Создаёт 10 фиктивных пользователей и регистрирует их на турнир.

    Используется для отладки турнирной сетки, драфтов и т.д.
    Доступен только администраторам и только в development окружении.
    """
    # Guard: только development
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Dev endpoints are disabled in production"
        )

    # Проверяем что турнир существует
    tournament_result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = tournament_result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    created_user_ids = []
    created_participants = []

    for i in range(10):
        # Генерируем уникальные данные
        suffix = secrets.token_hex(4)
        username = f"BotUser_{suffix}"
        discord_id = str(900000000000000000 + i * 100000 + hash(suffix) % 10000)
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{i % 5}.png"

        # Проверяем что discord_id уникален (на случай коллизий)
        existing_discord = await db.execute(
            select(User).where(User.discord_id == discord_id)
        )
        if existing_discord.scalar_one_or_none():
            discord_id = str(int(discord_id) + 1)

        user = User(
            discord_id=discord_id,
            username=username,
            display_name=username,
            avatar_url=avatar_url,
            role="player",
            is_ghost=False,
        )
        db.add(user)
        await db.flush()  # получаем user.id до commit

        # Создаём заявку на участие (сразу одобренную)
        # Первые два участника — капитаны
        is_captain = i < 2
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            user_id=user.id,
            status="registered",
            is_allowed=True,
            is_captain=is_captain,
        )
        db.add(participant)
        created_user_ids.append(user.id)
        created_participants.append(participant)

    await db.commit()

    return {
        "message": f"Successfully seeded 10 participants for tournament {tournament_id} (first 2 are captains)",
        "user_ids": created_user_ids,
        "captain_ids": [created_user_ids[0], created_user_ids[1]],
        "tournament_id": tournament_id,
    }


@router.post("/tournaments/{tournament_id}/reset-draft")
async def reset_draft_for_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    [DEV ONLY] Сбросить драфт турнира: удалить сессию, пики, капитанов.

    Возвращает статус турнира в "registration".
    Доступен только администраторам и только в development окружении.
    """
    # Guard: только development
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Dev endpoints are disabled in production"
        )

    # Проверяем что турнир существует
    tournament_result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = tournament_result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Ищем DraftSession по tournament_id
    draft_session_result = await db.execute(
        select(DraftSession).where(DraftSession.tournament_id == tournament_id)
    )
    draft_session = draft_session_result.scalar_one_or_none()

    if not draft_session:
        raise HTTPException(status_code=404, detail="No draft session found for this tournament")

    # Удаляем все DraftPick (каскад через relationship, но на всякий случай)
    await db.execute(
        DraftPick.__table__.delete().where(DraftPick.draft_session_id == draft_session.id)
    )

    # Удаляем все DraftCaptain (каскад через relationship)
    await db.execute(
        DraftCaptain.__table__.delete().where(DraftCaptain.draft_session_id == draft_session.id)
    )

    # Удаляем саму DraftSession
    await db.delete(draft_session)

    # Сбрасываем статус турнира обратно на "registration"
    tournament.status = "registration"

    await db.commit()

    return {
        "status": "ok",
        "message": "Draft reset successful",
        "tournament_id": tournament_id,
    }


@router.delete("/tournaments/{tournament_id}/participants")
async def delete_all_participants_for_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    [DEV ONLY] Удалить ВСЕХ участников турнира (только TournamentParticipant, не User).

    Доступен только администраторам и только в development окружении.
    """
    # Guard: только development
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Dev endpoints are disabled in production"
        )

    # Проверяем что турнир существует
    tournament_result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id)
    )
    tournament = tournament_result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Находим все записи участников
    participants_result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.tournament_id == tournament_id)
    )
    participants = participants_result.scalars().all()
    count = len(participants)

    # Удаляем только TournamentParticipant записи (не User)
    for participant in participants:
        await db.delete(participant)

    await db.commit()

    return {
        "status": "ok",
        "message": "All participants removed",
        "count": count,
        "tournament_id": tournament_id,
    }
