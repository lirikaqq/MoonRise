# app/routers/draft.py — админские эндпоинты драфта
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.schemas.draft import DraftSetupRequest, DraftSetupResponse
from app.services.draft_service import setup_draft_session, start_draft, complete_draft_session
from app.redis_client import get_redis_client
import redis.asyncio as redis

router = APIRouter(prefix="/api/admin/draft", tags=["Draft Admin"])


@router.post("/{tournament_id}/setup", response_model=DraftSetupResponse)
async def setup_draft(
    tournament_id: int,
    setup_data: DraftSetupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    draft_session = await setup_draft_session(
        db=db, tournament_id=tournament_id, setup_data=setup_data
    )
    return DraftSetupResponse(
        draft_session_id=draft_session.id,
        message="Draft session setup successfully. Ready to start."
    )


@router.post("/{session_id}/start", status_code=200)
async def start_draft_endpoint(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_admin)
):
    """
    [АДМИН] Запускает драфт.
    """
    await start_draft(db=db, redis_client=redis_client, session_id=session_id)
    return {"message": "Draft started successfully"}


@router.post("/{session_id}/complete")
async def complete_draft_endpoint(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_admin)
):
    """
    [АДМИН] Завершает драфт: создаёт команды из DraftPick.

    Вызывается автоматически после последнего пика,
    но админ может вызвать вручную если что-то пошло не так.
    """
    teams = await complete_draft_session(db=db, redis_client=redis_client, session_id=session_id)

    return {
        "message": "Draft completed successfully. Teams created.",
        "teams": [
            {
                "team_id": team.id,
                "team_name": team.name,
                "captain_user_id": team.captain_user_id
            }
            for team in teams
        ]
    }