from fastapi import APIRouter, Depends, HTTPException
from app.services.sheets_service import SheetsService
from app.db.session import AsyncSession
from app.db.models import Tournament, Participant, User
from sqlalchemy import select
from app.api.auth import AdminRequired

router = APIRouter()

@router.put("/api/tournaments/{tournament_id}/sheet-id")
async def update_sheet_id(tournament_id: int, data: dict, session: AsyncSession = Depends(), current_admin = Depends(AdminRequired)):
    sheet_id = data.get("sheet_id")
    if not sheet_id:
        raise HTTPException(status_code=400, detail="sheet_id is required")

    tournament = await session.execute(select(Tournament).filter(Tournament.id == tournament_id))
    tournament = tournament.scalar()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    tournament.google_sheet_id = sheet_id
    session.add(tournament)
    await session.commit()

    return {"success": True, "sheet_id": sheet_id}

@router.post("/api/tournaments/{tournament_id}/export-to-sheets")
async def export_to_sheets(tournament_id: int, session: AsyncSession = Depends(), current_admin = Depends(AdminRequired)):
    tournament = await session.execute(select(Tournament).filter(Tournament.id == tournament_id))
    tournament = tournament.scalar()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if not tournament.google_sheet_id:
        raise HTTPException(status_code=400, detail="Sheet ID не указан")

    participants = await session.execute(
        select(Participant).join(User, Participant.user_id == User.id).filter(Participant.tournament_id == tournament_id)
    )
    participants = participants.scalars().all()

    participants_data = []
    for participant in participants:
        user = participant.user
        participant_data = {
            "discord": user.discord_username or user.username,
            "battle_tag": user.battle_tag,
            "alt_battle_tags": "",
            "primary_role": participant.application_data or "",
            "secondary_role": "",
            "wants_captain": participant.is_captain,
            "notes": "",
            "division": user.division or "",
            "approved": participant.is_allowed,
            "banned": participant.status == "banned",
            "checked_in": participant.checkedin_at is not None
        }
        participants_data.append(participant_data)

    sheets_service = SheetsService()
    result = await sheets_service.export_participants(tournament.google_sheet_id, tournament.title, participants_data)

    return result