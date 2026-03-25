from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.services.discord_oauth import (
    get_discord_login_url,
    exchange_code_for_token,
    get_discord_user
)
from app.core.security import create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/discord")
async def discord_login():
    """Редирект на страницу авторизации Discord."""
    login_url = get_discord_login_url()
    return RedirectResponse(url=login_url)


@router.get("/discord/callback")
async def discord_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Callback после авторизации Discord."""
    
    # 1. Обмениваем code на access_token
    token_data = await exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to get Discord token")
    
    discord_access_token = token_data.get("access_token")
    
    # 2. Получаем информацию о пользователе Discord
    discord_user = await get_discord_user(discord_access_token)
    if not discord_user:
        raise HTTPException(status_code=400, detail="Failed to get Discord user")
    
    discord_id = discord_user["id"]
    username = discord_user["username"]
    avatar_hash = discord_user.get("avatar")
    
    # Формируем URL аватара
    if avatar_hash:
        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
    else:
        avatar_url = None
    
    # 3. Ищем или создаём пользователя в БД
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()
    
    if user:
        # Обновляем данные
        user.username = username
        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()
    else:
        # Создаём нового пользователя
        user = User(
            discord_id=discord_id,
            username=username,
            avatar_url=avatar_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
    
    await db.commit()
    await db.refresh(user)
    
    # 4. Создаём JWT токен
    jwt_token = create_access_token(data={
        "sub": str(user.id),
        "discord_id": user.discord_id,
        "username": user.username,
    })
    
    # 5. Редиректим на фронтенд с токеном
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/me")
async def get_current_user_info(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о текущем пользователе по токену."""
    from app.core.security import decode_access_token
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "discord_id": user.discord_id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "role": user.role if user.role else "player",
        "division": user.division,
    }