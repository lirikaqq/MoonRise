from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.services.discord_oauth import (
    get_discord_login_url,
    exchange_code_for_token,
    get_discord_user
)
from app.core.security import create_access_token, decode_access_token
from app.config import settings

# УБРАЛ префикс здесь, так как он УЖЕ ЕСТЬ в main.py!
router = APIRouter(tags=["Auth"])
security = HTTPBearer()

@router.get("/discord")
async def discord_login():
    login_url = get_discord_login_url()
    return RedirectResponse(url=login_url)

@router.get("/discord/callback")
async def discord_callback(code: str, db: AsyncSession = Depends(get_db)):
    token_data = await exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to get Discord token")

    discord_access_token = token_data.get("access_token")
    discord_user = await get_discord_user(discord_access_token)
    if not discord_user:
        raise HTTPException(status_code=400, detail="Failed to get Discord user")

    discord_id = discord_user["id"]
    username = discord_user["username"]
    avatar_hash = discord_user.get("avatar")
    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
        if avatar_hash else None
    )

    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()

    if user:
        user.username = username
        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()
    else:
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

    jwt_token = create_access_token(data={
        "sub": str(user.id),
        "discord_id": user.discord_id,
        "username": user.username,
    })

    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


class TokenRequest(BaseModel):
    discord_id: str

@router.post("/token")
async def generate_token(request: TokenRequest, db: AsyncSession = Depends(get_db)):
    """Генерация JWT токена по discord_id (только для тестирования)"""
    
    # Используем асинхронный поиск, как и во всем твоем коде
    result = await db.execute(select(User).where(User.discord_id == request.discord_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in Database")

    access_token = create_access_token({
        "sub": str(user.id),
        "discord_id": user.discord_id,
        "username": user.username,
    })
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

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