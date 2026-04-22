from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Dict, Any
import math
import json

from app.database import get_db
from app.models.tournament import Tournament, TournamentParticipant
from app.models.match import Team
from app.models.user import User
from app.core.security import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


async def _get_tournament_or_404(tournament_id: int, db: AsyncSession) -> Tournament:
    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


async def _get_team_or_404(team_id: int, db: AsyncSession) -> Team:
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


async def _get_participant_or_404(participant_id: int, db: AsyncSession) -> TournamentParticipant:
    result = await db.execute(select(TournamentParticipant).where(TournamentParticipant.id == participant_id))
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


def _get_team_config(tournament: Tournament) -> Dict[str, Any]:
    """Возвращает team_config или дефолтные значения."""
    settings = tournament.structure_settings or {}
    return settings.get("team_config", {
        "team_size": 5,
        "role_limits": {"tank": 1, "dps": 2, "sup": 2}
    })


def _parse_role(participant: TournamentParticipant) -> str | None:
    """Безопасно извлекает primary_role из application_data."""
    if not participant.application_data:
        return None
    try:
        data = json.loads(participant.application_data) if isinstance(participant.application_data, str) else participant.application_data
        return data.get("primary_role")
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


# ==================== BALANCE PLACEHOLDER ====================

@router.post("/tournaments/{tournament_id}/teams/balance-placeholder", status_code=status.HTTP_201_CREATED)
async def balance_placeholder_teams(
    tournament_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Создаёт пустые команды-заглушки для mix-турнира."""
    tournament = await _get_tournament_or_404(tournament_id, db)

    if tournament.format != "mix":
        raise HTTPException(status_code=400, detail="Only allowed for mix format")

    # Проверка, что команд ещё нет
    team_count = await db.scalar(select(func.count()).where(Team.tournament_id == tournament_id))
    if team_count > 0:
        raise HTTPException(status_code=409, detail="Teams already exist")

    participants = await db.scalars(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.is_allowed == True
        )
    ).all()

    if not participants:
        raise HTTPException(status_code=400, detail="No approved participants")

    team_config = _get_team_config(tournament)
    team_size = team_config.get("team_size", 5)
    num_teams = math.ceil(len(participants) / team_size)

    teams = []
    for i in range(num_teams):
        team = Team(
            tournament_id=tournament_id,
            name=f"Team {i+1}",
            source="mix_placeholder",
            is_confirmed=False
        )
        db.add(team)
        teams.append(team)

    await db.commit()
    for team in teams:
        await db.refresh(team)

    return {
        "message": f"Created {num_teams} placeholder teams",
        "teams": [{"id": t.id, "name": t.name} for t in teams]
    }


# ==================== MANUAL TEAM ====================

@router.post("/tournaments/{tournament_id}/teams/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_team(
    tournament_id: int,
    body: dict,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Создаёт команду вручную."""
    await _get_tournament_or_404(tournament_id, db)

    name = body.get("name")
    if not name or not isinstance(name, str):
        raise HTTPException(status_code=400, detail="Team name is required")

    team = Team(
        tournament_id=tournament_id,
        name=name.strip(),
        source="manual",
        is_confirmed=False
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return {"id": team.id, "name": team.name, "source": team.source, "is_confirmed": team.is_confirmed}


# ==================== ADD PARTICIPANT ====================

@router.post("/tournaments/{tournament_id}/teams/{team_id}/add/{participant_id}")
async def add_participant_to_team(
    tournament_id: int,
    team_id: int,
    participant_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Добавляет участника в команду с полной валидацией."""
    tournament = await _get_tournament_or_404(tournament_id, db)
    team = await _get_team_or_404(team_id, db)
    participant = await _get_participant_or_404(participant_id, db)

    if participant.tournament_id != tournament_id:
        raise HTTPException(status_code=400, detail="Participant not in this tournament")
    if not participant.is_allowed:
        raise HTTPException(status_code=400, detail="Participant is not approved")
    if participant.team_id is not None:
        raise HTTPException(status_code=400, detail="Participant already in another team")
    if team.tournament_id != tournament_id:
        raise HTTPException(status_code=400, detail="Team does not belong to this tournament")

    # Проверка размера команды
    current_size = await db.scalar(
        select(func.count()).where(TournamentParticipant.team_id == team_id)
    )
    team_config = _get_team_config(tournament)
    if current_size >= team_config.get("team_size", 5):
        raise HTTPException(status_code=400, detail="Team is full")

    # Проверка роли
    role = _parse_role(participant)
    if role:
        role_limits = team_config.get("role_limits", {"tank": 1, "dps": 2, "sup": 2})
        limit = role_limits.get(role, 0)
        if limit > 0:
            current_role_count = await db.scalar(
                select(func.count())
                .where(TournamentParticipant.team_id == team_id)
                .where(TournamentParticipant.application_data.contains(f'"primary_role": "{role}"'))
            )
            if current_role_count >= limit:
                raise HTTPException(status_code=400, detail=f"Role limit reached for {role}")

    participant.team_id = team_id
    await db.commit()
    await db.refresh(participant)

    return {"message": "Participant successfully added to team"}


# ==================== REMOVE PARTICIPANT ====================

@router.delete("/tournaments/{tournament_id}/teams/{team_id}/remove/{participant_id}")
async def remove_participant_from_team(
    tournament_id: int,
    team_id: int,
    participant_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Убирает участника из команды."""
    await _get_tournament_or_404(tournament_id, db)
    await _get_team_or_404(team_id, db)
    participant = await _get_participant_or_404(participant_id, db)

    if participant.team_id != team_id:
        raise HTTPException(status_code=400, detail="Participant is not in this team")

    participant.team_id = None
    await db.commit()

    return {"message": "Participant removed from team"}


# ==================== DELETE TEAM ====================

@router.delete("/tournaments/{tournament_id}/teams/{team_id}")
async def delete_team(
    tournament_id: int,
    team_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Удаляет команду и освобождает участников."""
    await _get_tournament_or_404(tournament_id, db)
    team = await _get_team_or_404(team_id, db)

    if team.tournament_id != tournament_id:
        raise HTTPException(status_code=400, detail="Team does not belong to this tournament")

    # Освобождаем всех участников
    await db.execute(
        update(TournamentParticipant)
        .where(TournamentParticipant.team_id == team_id)
        .values(team_id=None)
    )

    await db.delete(team)
    await db.commit()

    return {"message": "Team successfully deleted"}


# ==================== CONFIRM TEAM ====================

@router.put("/tournaments/{tournament_id}/teams/{team_id}/confirm")
async def confirm_team(
    tournament_id: int,
    team_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Подтверждает команду."""
    await _get_tournament_or_404(tournament_id, db)
    team = await _get_team_or_404(team_id, db)

    if team.tournament_id != tournament_id:
        raise HTTPException(status_code=400, detail="Team does not belong to this tournament")

    team.is_confirmed = True
    await db.commit()
    await db.refresh(team)

    return {"message": "Team confirmed", "team": {"id": team.id, "is_confirmed": team.is_confirmed}}