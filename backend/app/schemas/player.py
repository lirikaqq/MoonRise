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


# --- Profile Stats Schemas ---
class PlayerProfileStatsResponse(BaseModel):
    total_matches: int
    wins: int
    losses: int
    winrate: float
    kda_ratio: float
    elims_avg: float
    deaths_avg: float
    assists_avg: float
    damage_avg: float
    healing_avg: float
    mvp_count: int
    svp_count: int
    playtime_hours: float
    maps_count: int


class HeroStatsResponse(BaseModel):
    hero_name: str
    time_played: int
    matches_played: int
    eliminations: int
    deaths: int
    hero_damage_dealt: float
    healing_dealt: float
    kda: float


class TopHeroesResponse(BaseModel):
    heroes: List[HeroStatsResponse]


class MatchHistoryItemResponse(BaseModel):
    match_id: int
    encounter_id: int
    tournament_id: int
    tournament_name: str
    map_name: str
    stage: Optional[str] = None
    team1_name: str
    team2_name: str
    team1_score: int
    team2_score: int
    result: str  # "win", "loss", "unknown"
    eliminations: int
    final_blows: int
    deaths: int
    hero_damage_dealt: float
    healing_dealt: float
    damage_blocked: float
    objective_kills: int
    kda: float
    is_mvp: bool
    is_svp: bool
    main_hero: Optional[str] = None
    heroes: List[str] = []