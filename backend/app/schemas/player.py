from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- BattleTag Schemas ---
class BattleTagBase(BaseModel):
    tag: str
    is_primary: bool = False

class BattleTagCreate(BattleTagBase):
    pass

class BattleTagSchema(BattleTagBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# --- User Schemas ---
class PlayerBase(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    role: Optional[str] = None        # Добавили, чтобы можно было отображать бейдж
    division: Optional[str] = None    # Добавили для карточки
    is_ghost: bool = False            # 👇 ДОБАВИЛИ, чтобы фронт знал о призраках
    
    class Config:
        from_attributes = True


class PlayerCreate(BaseModel):
    discord_id: str
    username: str
    avatar_url: Optional[str] = None


class PlayerProfileResponse(PlayerBase):
    discord_id: Optional[str] = None  # 👇 ИСПРАВЛЕНО: Теперь может быть None
    battletags: List[BattleTagSchema] = []
    
    class Config:
        from_attributes = True


class PlayerUpdate(BaseModel):
    primary_battletag: Optional[str] = None
    division: Optional[str] = None