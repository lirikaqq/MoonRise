from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.player_service import PlayerService
from app.schemas.player import (
    PlayerProfileResponse,
    PlayerProfileUpdate,
    BattleTagCreate,
    BattleTagResponse,
)
from app.core.security import decode_access_token

router = APIRouter(prefix="/players", tags=["players"])


def get_current_user_id(token: str = None) -> int:
    """Получить ID текущего пользователя из JWT токена."""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return int(user_id)


@router.get("/me", response_model=PlayerProfileResponse)
async def get_current_player(
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить профиль текущего игрока."""
    user_id = get_current_user_id(token)
    player = await PlayerService.get_player_by_id(db, user_id)
    return player


@router.get("/{player_id}", response_model=PlayerProfileResponse)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить профиль игрока по ID."""
    player = await PlayerService.get_player_by_id(db, player_id)
    return player


@router.put("/me", response_model=PlayerProfileResponse)
async def update_current_player(
    profile_update: PlayerProfileUpdate,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Обновить свой профиль."""
    user_id = get_current_user_id(token)
    
    player = await PlayerService.get_player_by_id(db, user_id)
    
    # Обновляем только указанные поля
    if profile_update.division is not None:
        player.division = profile_update.division
    
    await db.commit()
    await db.refresh(player)
    return player


@router.post("/me/battletag", response_model=BattleTagResponse)
async def add_battletag(
    tag_data: BattleTagCreate,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Добавить баттлтег."""
    user_id = get_current_user_id(token)
    new_tag = await PlayerService.add_battletag(db, user_id, tag_data)
    return new_tag


@router.delete("/me/battletag/{tag_id}")
async def delete_battletag(
    tag_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Удалить баттлтег."""
    user_id = get_current_user_id(token)
    result = await PlayerService.delete_battletag(db, user_id, tag_id)
    return result


@router.put("/me/battletag/{tag_id}/primary", response_model=BattleTagResponse)
async def set_primary_battletag(
    tag_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Сделать баттлтег основным."""
    user_id = get_current_user_id(token)
    tag = await PlayerService.set_primary_battletag(db, user_id, tag_id)
    return tag