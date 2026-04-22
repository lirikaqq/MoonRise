from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.constants import VALID_TOURNAMENT_STATUSES, VALID_ROLES, VALID_RANKS


# ====================== DRAFT SESSION ======================

class DraftSessionResponse(BaseModel):
    id: int
    tournament_id: int
    status: str
    pick_time_seconds: int
    team_size: int
    current_pick_index: int
    pick_order: List[int]
    role_slots: Dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ====================== TOURNAMENT ======================

class TournamentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    format: str = Field(..., pattern="^(mix|draft)$")
    cover_url: Optional[str] = None

    description_general: Optional[str] = None
    description_dates: Optional[str] = None
    description_requirements: Optional[str] = None

    start_date: datetime
    end_date: datetime
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None

    status: str = Field(default="upcoming")
    max_participants: Optional[int] = 100
    is_featured: bool = Field(default=False)

    structure_type: str = Field(default="SINGLE_ELIMINATION")
    structure_settings: Optional[Dict[str, Any]] = None
    twitch_channel: Optional[str] = Field(None, max_length=100)
    rules_url: Optional[str] = Field(None, max_length=255)
    google_sheet_id: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_TOURNAMENT_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {VALID_TOURNAMENT_STATUSES}")
        return v

    @field_validator('structure_type')
    @classmethod
    def validate_structure_type(cls, v: str) -> str:
        valid = ["SINGLE_ELIMINATION", "DOUBLE_ELIMINATION", "ROUND_ROBIN", "GROUPS_PLUS_PLAYOFF", "SWISS"]
        if v not in valid:
            raise ValueError(f"structure_type must be one of: {valid}")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v


class TournamentUpdate(BaseModel):
    """Обновление данных турнира (все поля опциональные)."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    format: Optional[str] = Field(None, pattern="^(mix|draft)$")
    cover_url: Optional[str] = None

    description_general: Optional[str] = None
    description_dates: Optional[str] = None
    description_requirements: Optional[str] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None
    status: Optional[str] = None
    max_participants: Optional[int] = None
    is_featured: Optional[bool] = None

    structure_type: Optional[str] = None
    structure_settings: Optional[Dict[str, Any]] = None
    twitch_channel: Optional[str] = Field(None, max_length=100)
    rules_url: Optional[str] = Field(None, max_length=255)
    
    # ← Добавлено для поддержки team_config
    team_config: Optional[Dict[str, Any]] = None

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["mix", "draft"]:
            raise ValueError("Format must be 'mix' or 'draft'")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_TOURNAMENT_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {VALID_TOURNAMENT_STATUSES}")
        return v


class TournamentResponse(BaseModel):
    id: int
    title: str
    format: str
    cover_url: Optional[str] = None
    description_general: Optional[str] = None
    description_dates: Optional[str] = None
    description_requirements: Optional[str] = None

    start_date: datetime
    end_date: datetime
    registration_open: Optional[datetime] = None
    registration_close: Optional[datetime] = None
    checkin_open: Optional[datetime] = None
    checkin_close: Optional[datetime] = None

    status: str
    max_participants: Optional[int] = None
    participants_count: int = 0
    is_featured: bool = False
    is_active: bool = True

    structure_type: str
    structure_settings: Optional[Dict[str, Any]] = None
    twitch_channel: Optional[str] = None
    rules_url: Optional[str] = None
    google_sheet_id: Optional[str] = None

    # Архитектурные поля
    team_config: Dict[str, Any] = Field(default_factory=dict)
    division: Optional[int] = None

    # Защита от MissingGreenlet
    draft_session: Optional[Dict[str, Any]] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class TournamentShortResponse(BaseModel):
    id: int
    title: str
    format: str
    cover_url: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: str
    participants_count: int
    max_participants: Optional[int] = None
    is_featured: bool = False
    structure_type: str

    model_config = ConfigDict(from_attributes=True)


# ====================== APPLICATIONS ======================

class ApplicationCreateMix(BaseModel):
    primary_role: str
    secondary_role: str
    bio: Optional[str] = Field(None, max_length=500)
    confirmed_friend_request: bool
    confirmed_rules: bool

    @field_validator('primary_role', 'secondary_role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Роль должна быть одной из: {VALID_ROLES}")
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
    rating_claimed: str
    battletag_id: Optional[int] = None
    new_battletag: Optional[str] = Field(None, max_length=50)

    @field_validator('rating_claimed')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        if v not in VALID_RANKS:
            raise ValueError("Rating must be one of valid ranks")
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
        if not self.battletag_id and not self.new_battletag:
            raise ValueError("Необходимо указать battletag_id или new_battletag")
        if self.battletag_id and self.new_battletag:
            raise ValueError("Укажите либо battletag_id, либо new_battletag — не оба")
        return self


class ApplicationResponse(BaseModel):
    id: int
    tournament_id: int
    user_id: int
    status: str
    is_allowed: bool
    metadata: Optional[Dict[str, Any]] = None
    registered_at: datetime
    updated_at: datetime
    user_username: Optional[str] = None
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationApprove(BaseModel):
    rating_approved: Optional[str] = None

    @field_validator('rating_approved')
    @classmethod
    def validate_rating(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_RANKS:
            raise ValueError("Rating must be one of valid ranks")
        return v


class ApplicationReject(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


# ====================== BRACKET ======================

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
    lower_bracket: Optional[List[BracketRound]] = None


# ====================== ADMIN ADD PARTICIPANT ======================

class AddParticipantRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    discord_tag: Optional[str] = Field(None, max_length=50)
    battletag_value: str = Field(..., min_length=3, max_length=50)
    primary_role: str
    secondary_role: Optional[str] = None
    division: Optional[int] = Field(None, ge=1, le=20)
    bio: Optional[str] = Field(None, max_length=500)
    is_captain: bool = False

    @field_validator('primary_role', 'secondary_role')
    @classmethod
    def validate_roles(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {VALID_ROLES}")
        return v

    model_config = ConfigDict(from_attributes=True)


# ====================== PLAYER REPLACEMENT ======================

class ReplacePlayerRequest(BaseModel):
    old_participant_id: int = Field(..., gt=0)
    new_participant_id: int = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class ReplacementResponse(BaseModel):
    id: int
    tournament_id: int
    team_id: int
    old_participant_id: int
    new_participant_id: int
    replaced_by_user_id: int
    replaced_at: datetime
    reason: Optional[str] = None
    previous_is_captain: bool

    old_participant: Optional[Dict[str, Any]] = None
    new_participant: Optional[Dict[str, Any]] = None
    replaced_by: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TeamWithHistoryResponse(BaseModel):
    team: Dict[str, Any]
    active_participants: List[Dict[str, Any]]
    replacement_history: List[ReplacementResponse]

    model_config = ConfigDict(from_attributes=True)