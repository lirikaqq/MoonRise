from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.homepage import HomepageSettings
from app.models.user import User
from app.core.security import decode_access_token

router = APIRouter(prefix="/homepage", tags=["homepage"])


class HomepageResponse(BaseModel):
    id: int
    tournament_id: Optional[int]
    title: str
    date_text: str
    description: str
    logo_url: Optional[str]
    hero_image_url: Optional[str]
    registration_text: str
    registration_url: str
    info_text: str
    info_url: str

    class Config:
        from_attributes = True


class HomepageUpdate(BaseModel):
    tournament_id: Optional[int] = None
    title: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    hero_image_url: Optional[str] = None
    registration_text: Optional[str] = None
    registration_url: Optional[str] = None
    info_text: Optional[str] = None
    info_url: Optional[str] = None


async def get_admin_user(authorization: str, db: AsyncSession) -> User:
    """Проверить что пользователь — админ."""
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
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_settings(db: AsyncSession) -> HomepageSettings:
    """Получить настройки (всегда id=1)."""
    result = await db.execute(select(HomepageSettings).where(HomepageSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = HomepageSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.get("/settings", response_model=HomepageResponse)
async def get_homepage_settings(db: AsyncSession = Depends(get_db)):
    """Получить настройки главной (публичный)."""
    settings = await get_settings(db)
    return settings


@router.put("/settings", response_model=HomepageResponse)
async def update_homepage_settings(
    data: HomepageUpdate,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки главной (только admin)."""
    await get_admin_user(authorization, db)
    settings = await get_settings(db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(settings)
    return settings