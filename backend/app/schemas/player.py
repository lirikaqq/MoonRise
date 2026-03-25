from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# BattleTag схемы
class BattleTagCreate(BaseModel):
    """Добавить новый баттлтег."""
    tag: str = Field(..., min_length=3, max_length=100)
    is_primary: bool = False


class BattleTagUpdate(BaseModel):
    """Обновить баттлтег."""
    tag: Optional[str] = None
    is_primary: Optional[bool] = None


class BattleTagResponse(BaseModel):
    """Ответ с баттлтегом."""
    id: int
    tag: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Профиль игрока схемы
class PlayerProfileResponse(BaseModel):
    """Полный профиль игрока."""
    id: int
    discord_id: str
    username: str
    avatar_url: Optional[str]
    role: str
    division: Optional[str]
    is_banned: bool
    reputation_score: int
    battletags: List[BattleTagResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlayerProfileUpdate(BaseModel):
    """Обновить профиль."""
    division: Optional[str] = None


class PlayerShortResponse(BaseModel):
    """Короткий профиль игрока."""
    id: int
    discord_id: str
    username: str
    avatar_url: Optional[str]
    role: str
    division: Optional[str]

    class Config:
        from_attributes = True