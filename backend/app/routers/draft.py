# app/routers/draft.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession # <-- Меняем импорт

from app.database import get_db
from app.core.security import get_current_user, get_current_admin # Убедимся, что все функции async
from app.models.user import User

from app.schemas.draft import DraftSetupRequest, DraftSetupResponse
from app.services.draft_service import setup_draft_session

from app.redis_client import get_redis_client # Импортируем зависимость для Redis
import redis.asyncio as redis
from app.services.draft_service import start_draft # Импортируем новую функцию
from app.services.draft_service import make_pick # Импорт новой функции
from app.schemas.draft import DraftPickRequest
from app.schemas.draft import DraftStateResponse # Добавляем импорт
from app.services.draft_service import get_draft_state # Добавляем импорт

router = APIRouter(prefix="/api/admin/draft", tags=["Draft Admin"])

# Добавляем async def
@router.post("/{tournament_id}/setup", response_model=DraftSetupResponse)
async def setup_draft(
    tournament_id: int,
    setup_data: DraftSetupRequest,
    db: AsyncSession = Depends(get_db), # <-- Меняем тип сессии
    current_user: User = Depends(get_current_admin) # Используем get_current_admin
):
    # Убираем проверку на админа, т.к. get_current_admin уже делает это
    
    # Добавляем await
    draft_session = await setup_draft_session(db=db, tournament_id=tournament_id, setup_data=setup_data)
    
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

public_router = APIRouter(prefix="/api/draft", tags=["Draft"])

@public_router.post("/{session_id}/pick", status_code=201)
async def make_pick_endpoint(
    session_id: int,
    pick_data: DraftPickRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user) # Обычный юзер, не админ
):
    """
    [КАПИТАН] Делает выбор игрока.
    """
    await make_pick(
        db=db, 
        redis_client=redis_client, 
        session_id=session_id, 
        pick_data=pick_data, 
        current_user_id=current_user.id
    )
    return {"message": "Pick successful"}

@public_router.get("/{session_id}", response_model=DraftStateResponse)
async def get_draft_state_endpoint(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # Проверяем, что юзер залогинен
):
    """
    [КАПИТАН] Получить полное текущее состояние драфта.
    """
    # TODO: Добавить проверку, что current_user является капитаном этого драфта.
    return await get_draft_state(db, session_id)