from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.database import get_db
from app.services.match_service import MatchService
from app.models.match import Encounter
from app.schemas.match import (
    TeamCreate, TeamResponse, TeamParticipantBrief, UserBrief,
    EncounterCreate, EncounterResponse,
    KillFeedItem, FirstBloodItem,
    PlayerMappingItem,
)
from app.core.security import decode_access_token
from app.models.user import User
from sqlalchemy import select

router = APIRouter(tags=["matches"])

async def get_current_admin(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token required")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


@router.post("/teams", response_model=TeamResponse)
async def create_team(
    data: TeamCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    return await MatchService.create_team(db, data)


@router.get("/teams/tournament/{tournament_id}", response_model=List[TeamResponse])
async def get_teams(tournament_id: int, db: AsyncSession = Depends(get_db)):
    teams = await MatchService.get_teams_by_tournament(db, tournament_id)
    result = []
    for team in teams:
        team_dict = TeamResponse.model_validate(team)
        # Преобразуем участников
        team_dict.participants = [
            TeamParticipantBrief.model_validate(p)
            for p in team.tournament_participants or []
        ]
        # Преобразуем капитана
        if team.captain:
            team_dict.captain = UserBrief.model_validate(team.captain)
        result.append(team_dict)
    return result


@router.post("/encounters", response_model=EncounterResponse)
async def create_encounter(
    data: EncounterCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    encounter = await MatchService.create_encounter(db, data)
    return {
        'id': encounter.id,
        'tournament_id': encounter.tournament_id,
        'team1_id': encounter.team1_id,
        'team2_id': encounter.team2_id,
        'team1_score': encounter.team1_score,
        'team2_score': encounter.team2_score,
        'winner_team_id': encounter.winner_team_id,
        'stage': encounter.stage_name,
        'round_number': encounter.round_number,
        'created_at': encounter.created_at,
        'team1': None,
        'team2': None,
        'matches': [],
    }


@router.get("/encounters/tournament/{tournament_id}", response_model=List[EncounterResponse])
async def get_tournament_encounters(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await MatchService.get_encounters_by_tournament(db, tournament_id)


@router.get("/encounters/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(encounter_id: int, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_encounter(db, encounter_id)


@router.post("/upload")
async def upload_log(
    file: UploadFile = File(...),
    encounter_id: Optional[int] = Form(None),
    tournament_id: Optional[int] = Form(None),
    map_number: Optional[int] = Form(None),
    player_mappings: Optional[str] = Form(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    mappings = []
    if player_mappings:
        try:
            raw = json.loads(player_mappings)
            mappings = [PlayerMappingItem(**m) for m in raw]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid player_mappings format")

    if encounter_id is None and tournament_id is None:
        raise HTTPException(status_code=400, detail="Either encounter_id or tournament_id is required")

    result = await MatchService.upload_log(
        db=db,
        file_content=content,
        file_name=file.filename,
        encounter_id=encounter_id,
        tournament_id=tournament_id,
        map_number=map_number,
        player_mappings=mappings
    )
    return result


@router.get("/player/{user_id}/history")
async def get_player_history(user_id: int, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_player_match_history(db, user_id)


@router.delete("/{match_id}")
async def delete_match(
    match_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    return await MatchService.delete_match(db, match_id)


@router.get("/{match_id}")
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_match(db, match_id)


@router.get("/{match_id}/killfeed", response_model=List[KillFeedItem])
async def get_match_killfeed(match_id: int, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_match_killfeed(db, match_id)


@router.get("/{match_id}/first-blood", response_model=List[FirstBloodItem])
async def get_match_first_blood(match_id: int, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_match_first_blood(db, match_id)


# ============================
# ADMIN: Result & Forfeit
# ============================
class EncounterResultBody(BaseModel):
    team1_score: Optional[int] = None
    team2_score: Optional[int] = None
    winner_team_id: Optional[int] = None


class ForfeitBody(BaseModel):
    loser_team_id: int  # ID команды, которой засчитывается поражение


class ReportResultBody(BaseModel):
    team1_score: int
    team2_score: int


@router.put("/admin/encounters/{encounter_id}/report-result")
async def report_encounter_result(
    encounter_id: int,
    body: ReportResultBody,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Сообщить результат встречи и автоматически продвинуть победителя
    в следующий раунд single-elimination сетки.
    """
    return await MatchService.report_encounter_result(
        db=db,
        encounter_id=encounter_id,
        team1_score=body.team1_score,
        team2_score=body.team2_score,
    )


# ============================
# ADMIN: Match Settings (Replace / Delete)
# ============================
class ReplaceTeamBody(BaseModel):
    old_team_id: int
    new_team_id: int

@router.put("/admin/encounters/{encounter_id}/replace")
async def replace_team_in_encounter(
    encounter_id: int,
    body: ReplaceTeamBody,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Заменить одну из команд в матче (например, при форс-мажоре)."""
    result = await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    enc = result.scalar_one_or_none()
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found")

    if body.old_team_id not in (enc.team1_id, enc.team2_id):
        raise HTTPException(status_code=400, detail="Team is not part of this encounter")
    if body.new_team_id not in (enc.team1_id, enc.team2_id) and body.new_team_id == body.old_team_id:
        raise HTTPException(status_code=400, detail="New team must be different")

    if enc.team1_id == body.old_team_id:
        enc.team1_id = body.new_team_id
    else:
        enc.team2_id = body.new_team_id

    await db.commit()
    await db.refresh(enc)
    return MatchService._encounter_to_dict(enc)


@router.delete("/admin/encounters/{encounter_id}")
async def delete_encounter(
    encounter_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Удалить встречу (предупреждение о нарушении сетки — на фронтенде)."""
    result = await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    enc = result.scalar_one_or_none()
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found")

    await db.delete(enc)
    await db.commit()
    return {"message": "Encounter deleted", "id": encounter_id}