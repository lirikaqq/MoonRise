# backend/app/schemas/tournament.py

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.constants import VALID_RANKS, VALID_ROLES, VALID_TOURNAMENT_STATUSES


# ==================== СУЩЕСТВУЮЩИЕ СХЕМЫ (НЕ ТРОГАЕМ) ====================

# backend/app/schemas/tournament.py
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class TournamentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    format: str = Field(..., pattern="^(mix|draft)$")
    cover_url: Optional[str] = None
    start_date: datetime = Field(..., example="2025-12-25T19:00:00Z")
    end_date: datetime = Field(..., example="2025-12-25T23:00:00Z")
    status: str = Field(default="upcoming")
    max_participants: Optional[int] = 100
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_TOURNAMENT_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {VALID_TOURNAMENT_STATUSES}")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v


class TournamentResponse(BaseModel):
    """Полный ответ турнира."""
    id: int
    title: str
    description: Optional[str]
    format: str
    cover_url: Optional[str]
    start_date: datetime
    end_date: datetime
    registration_open: Optional[datetime]
    registration_close: Optional[datetime]
    checkin_open: Optional[datetime]
    checkin_close: Optional[datetime]
    status: str
    max_participants: Optional[int]
    participants_count: int
    is_featured: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TournamentShortResponse(BaseModel):
    """Короткий ответ турнира (для списка)."""
    id: int
    title: str
    format: str
    cover_url: Optional[str]
    start_date: datetime
    end_date: datetime
    status: str
    participants_count: int
    max_participants: Optional[int]
    is_featured: bool

    class Config:
        from_attributes = True


# ==================== НОВЫЕ СХЕМЫ ДЛЯ ЗАЯВОК ====================
class ApplicationCreateMix(BaseModel):
    """
    Заявка на mix-турнир.
    """
    primary_role: str = Field(..., description="Основная роль")
    secondary_role: str = Field(..., description="Дополнительная роль")
    bio: Optional[str] = Field(None, max_length=500)
    
    # НОВЫЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ДЛЯ ВСЕХ ТУРНИРОВ
    confirmed_friend_request: bool = Field(..., description="Подтверждение добавления в друзья")
    confirmed_rules: bool = Field(..., description="Согласие с регламентом")

    @field_validator('primary_role', 'secondary_role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Роль должна быть одной из: {', '.join(VALID_ROLES)}")
        return v

    @field_validator('confirmed_friend_request', 'confirmed_rules')
    @classmethod
    def validate_checkboxes(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Необходимо отметить все обязательные чекбоксы")
        return v

    @model_validator(mode='after')
    def validate_roles_different(self) -> 'ApplicationCreateMix':
        if self.primary_role == self.secondary_role:
            raise ValueError("Основная и дополнительная роли не могут совпадать")
        if self.primary_role == "flex" and self.secondary_role == "flex":
            raise ValueError("Нельзя выбрать flex для обеих ролей")
        return self


class ApplicationCreateDraft(ApplicationCreateMix):
    """
    Заявка на draft-турнир.
    """
    rating_claimed: str = Field(..., description="Рейтинг игрока")

    battletag_id: Optional[int] = Field(None, description="ID существующего BattleTag")
    new_battletag: Optional[str] = Field(None, max_length=50, description="Новый BattleTag")

    @field_validator('rating_claimed')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        if v not in VALID_RANKS:
            raise ValueError(f"Рейтинг должен быть одним из допустимых значений")
        return v

    @field_validator('new_battletag')
    @classmethod
    def validate_battletag_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r'^[a-zA-Z0-9]{3,12}#[0-9]{4,5}$', v):
            raise ValueError("BattleTag должен быть в формате Name#12345")
        return v

    @model_validator(mode='after')
    def validate_battletag_provided(self) -> 'ApplicationCreateDraft':
        # Проверяем BattleTag
        if not self.battletag_id and not self.new_battletag:
            raise ValueError("Необходимо указать battletag_id или new_battletag")
        if self.battletag_id and self.new_battletag:
            raise ValueError("Укажите либо battletag_id, либо new_battletag — не оба")
        return self



class ApplicationResponse(BaseModel):
    """
    Ответ с информацией о заявке.
    Используется для юзера (его заявка) и для админа (список заявок).
    """
    id: int
    tournament_id: int
    user_id: int
    status: str                      # pending / registered / rejected
    is_allowed: bool
    metadata: Optional[Dict[str, Any]]
    registered_at: datetime
    updated_at: datetime

    # Данные юзера (заполняются на уровне endpoint'а)
    user_username: Optional[str] = None
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationApprove(BaseModel):
    """
    Апрув заявки админом.
    Для draft-турниров можно скорректировать рейтинг.
    """
    rating_approved: Optional[str] = Field(
        None,
        description="Одобренный рейтинг (только для draft-турниров)"
    )

    @field_validator('rating_approved')
    @classmethod
    def validate_rating(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_RANKS:
            raise ValueError(f"Рейтинг должен быть одним из допустимых значений")
        return v


class ApplicationReject(BaseModel):
    """
    Отклонение заявки админом.
    """
    reason: Optional[str] = Field(None, max_length=500, description="Причина отклонения")

class TournamentUpdate(BaseModel):
    """Обновление данных турнира (все поля опциональные)."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    format: Optional[str] = Field(None, pattern="^(mix|draft)$")
    cover_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None
    status: Optional[str] = None
    max_participants: Optional[int] = None
    is_featured: Optional[bool] = None

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["mix", "draft"]:
            raise ValueError("Format must be 'mix' or 'draft'")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in [
            "upcoming", "registration", "checkin",
            "draft", "ongoing", "completed", "cancelled"
        ]:
            raise ValueError("Invalid tournament status")
        return v
    
# === СХЕМЫ ДЛЯ СЕТКИ (BRACKET) ===

class BracketTeam(BaseModel):
    name: str
    score: int
    isWinner: bool

class BracketMatch(BaseModel):
    id: int
    isEmpty: bool = False
    team1: Optional[BracketTeam] = None
    team2: Optional[BracketTeam] = None

class BracketRound(BaseModel):
    round_name: str
    matches: List[BracketMatch]

class BracketResponse(BaseModel):
    upper_bracket: List[BracketRound]
    # lower_bracket: List[BracketRound] = [] # Задел для нижней сетки