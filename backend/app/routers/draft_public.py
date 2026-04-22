# app/routers/draft_public.py — публичные эндпоинты драфта (для капитанов)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.redis_client import get_redis_client
import redis.asyncio as redis
from app.services.draft_service import make_pick, get_draft_state
from app.schemas.draft import DraftPickRequest, DraftStateResponse

router = APIRouter(prefix="/api/draft", tags=["Draft"])


@router.post("/{session_id}/pick", status_code=201)
async def make_pick_endpoint(
    session_id: int,
    pick_data: DraftPickRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    [КАПИТАН] Делает выбор игрока. Админ может пикать за любого капитана.
    """
    is_admin = current_user.role == "admin"
    await make_pick(
        db=db,
        redis_client=redis_client,
        session_id=session_id,
        pick_data=pick_data,
        current_user_id=current_user.id,
        is_admin=is_admin
    )
    return {"message": "Pick successful"}


@router.get("/{session_id}", response_model=DraftStateResponse)
async def get_draft_state_endpoint(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить полное текущее состояние драфта.
    TODO: Добавить проверку, что current_user является капитаном этого драфта.
    """
    return await get_draft_state(db, session_id)
