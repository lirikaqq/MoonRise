# app/schemas/draft.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class DraftSetupRequest(BaseModel):
    # Массив ID юзеров (капитанов) СТРОГО В ПОРЯДКЕ их ходов (от 1-го к 16-му)
    captain_user_ids: List[int] = Field(..., min_length=2, description="Ordered list of captain User IDs")
    
    # Названия команд. Ключ - ID юзера (капитана), значение - название команды.
    # Пример: {1: "Team Alpha", 42: "Team Bravo"}
    team_names: Dict[int, str]
    
    # Настройки
    pick_time_seconds: int = Field(default=90, ge=10, le=300) # Сколько секунд на 1 пик
    team_size: int = Field(default=4, ge=1, le=10) # Сколько пиков делает 1 капитан
    
    # Лимиты по ролям на команду (чтобы не набрали 4 танков)
    role_slots: Dict[str, int] = Field(
        default={"tank": 1, "dps": 2, "support": 2},
    )

    @field_validator("team_names")
    def validate_team_names(cls, v, info):
        # Проверяем, что админ не забыл указать название команды для кого-то из капитанов
        captains = info.data.get("captain_user_ids", [])
        for cap_id in captains:
            if cap_id not in v:
                raise ValueError(f"Team name missing for captain user_id: {cap_id}")
        return v

class DraftSetupResponse(BaseModel):
    draft_session_id: int
    message: str

class DraftPickRequest(BaseModel):
    picked_user_id: int
    assigned_role: str # "tank", "dps", "support"

class DraftStateCaptain(BaseModel):
    id: int
    user_id: int
    username: str
    team_name: str
    pick_position: int

class DraftStatePick(BaseModel):
    pick_number: int
    round_number: int
    captain_id: int # ID капитана (DraftCaptain)
    team_name: str
    picked_user_id: int
    picked_user_name: str
    assigned_role: str

class DraftStatePlayer(BaseModel):
    user_id: int
    username: str
    primary_role: str
    secondary_role: str
    rating_approved: str

class DraftStateResponse(BaseModel):
    session_id: int
    status: str
    pick_time_seconds: int
    current_pick_index: int
    current_pick_deadline: Optional[datetime]
    
    pick_order: List[int] # Массив user_id капитанов
    role_slots: Dict[str, int]
    
    captains: List[DraftStateCaptain]
    picks: List[DraftStatePick]
    player_pool: List[DraftStatePlayer]