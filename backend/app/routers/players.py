from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.services.player_service import PlayerService
from app.schemas.player import PlayerProfileResponse, PlayerUpdate, PlayerBase
from app.core.security import get_current_user_from_token
# Важно: предположим, что у тебя есть аналогичный хелпер для админа
# Если нет, можно временно закомментировать защиту роута
# from app.core.security import get_current_admin_from_token

router = APIRouter(tags=["players"])

@router.get("/", response_model=List[PlayerBase])
async def get_players(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Получаем игроков из сервиса
    players_list = await PlayerService.get_all_players(db, skip=skip, limit=limit)
    
    # 👇 ВОТ ЭТА СТРОКА САМАЯ ВАЖНАЯ 👇
    print("--- DEBUG: PLAYERS FROM DB ---", players_list)
    # 👇 И ВОТ ЭТА 👇
    if players_list:
        print("--- DEBUG: FIRST PLAYER OBJECT ---", players_list[0].__dict__)

    return players_list

@router.get("/{player_id}", response_model=PlayerProfileResponse)
async def get_player_by_id(player_id: int, db: AsyncSession = Depends(get_db)):
    player_profile = await PlayerService.get_player_profile(db, player_id)
    if not player_profile:
        raise HTTPException(status_code=404, detail="Player not found")
    return player_profile

@router.get("/{player_id}/tournaments")
async def get_player_tournaments_history(player_id: int, db: AsyncSession = Depends(get_db)):
    return await PlayerService.get_player_tournaments(db, player_id)

@router.put("/{user_id}", response_model=PlayerProfileResponse)
async def update_player_profile(
    user_id: int,
    data: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
):
    if current_user.get("id") != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You can only edit your own profile")
    updated_user = await PlayerService.update_player(db, user_id=user_id, data=data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Player not found")
    return await PlayerService.get_player_profile(db, updated_user.id)

# 👇 НОВЫЙ ЭНДПОИНТ 👇
@router.delete("/{player_id}", status_code=200)
async def delete_player(
    player_id: int,
    db: AsyncSession = Depends(get_db),
    # Раскомментируй строку ниже, чтобы защитить эндпоинт,
    # и убедись, что get_current_admin_from_token существует
    # current_admin: dict = Depends(get_current_admin_from_token),
):
    """Удаляет игрока и всю его статистику (только для админов)."""
    deleted_player = await PlayerService.delete_player(db, player_id)
    if not deleted_player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return {
        "message": f"Player '{deleted_player.username}' and all associated data have been deleted.", 
        "id": player_id
    }