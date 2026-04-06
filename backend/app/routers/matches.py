from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.database import get_db
from app.services.match_service import MatchService
from app.schemas.match import (
    TeamCreate, TeamResponse,
    EncounterCreate, EncounterResponse,
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
    return await MatchService.get_teams_by_tournament(db, tournament_id)


@router.post("/encounters", response_model=EncounterResponse)
async def create_encounter(
    data: EncounterCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    return await MatchService.create_encounter(db, data)


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
    encounter_id: int = Form(...),
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

    result = await MatchService.upload_log(
        db=db,
        file_content=content,
        file_name=file.filename,
        encounter_id=encounter_id,
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