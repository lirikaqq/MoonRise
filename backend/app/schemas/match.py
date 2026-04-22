from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeamCreate(BaseModel):
    name: str
    tournament_id: int
    captain_user_id: Optional[int] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    tournament_id: int
    captain_user_id: Optional[int] = None
    created_at: datetime

    # Вложенные данные: участники турнира, привязанные к команде
    participants: List['TeamParticipantBrief'] = []
    captain: Optional['UserBrief'] = None

    class Config:
        from_attributes = True


class TeamBriefResponse(BaseModel):
    """Упрощённая схема команды для использования в EncounterResponse.
    Не загружает captain/participants — избегает MissingGreenlet ошибок."""
    id: int
    name: str
    tournament_id: int
    captain_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TeamParticipantBrief(BaseModel):
    id: int
    user_id: int
    status: str
    is_captain: bool = False

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None

    class Config:
        from_attributes = True


class EncounterCreate(BaseModel):
    tournament_id: int
    team1_id: int
    team2_id: int
    stage: Optional[str] = None
    round_number: Optional[int] = None


class EncounterResponse(BaseModel):
    id: int
    tournament_id: int
    team1_id: int
    team2_id: int
    team1_score: int
    team2_score: int
    winner_team_id: Optional[int] = None
    stage: Optional[str] = None
    round_number: Optional[int] = None
    created_at: datetime
    team1: Optional['TeamBriefResponse'] = None
    team2: Optional['TeamBriefResponse'] = None
    matches: Optional[List['MatchShortResponse']] = []

    class Config:
        from_attributes = True


class MatchShortResponse(BaseModel):
    id: int
    map_name: str
    game_mode: Optional[str] = None
    duration_seconds: Optional[float] = None
    map_number: Optional[int] = None
    winner_team_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MatchPlayerHeroResponse(BaseModel):
    id: int
    hero_name: str
    eliminations: int = 0
    final_blows: int = 0
    deaths: int = 0
    all_damage_dealt: float = 0
    barrier_damage_dealt: float = 0
    hero_damage_dealt: float = 0
    healing_dealt: float = 0
    healing_received: float = 0
    self_healing: float = 0
    damage_taken: float = 0
    damage_blocked: float = 0
    defensive_assists: int = 0
    offensive_assists: int = 0
    objective_kills: int = 0
    ultimates_earned: int = 0
    ultimates_used: int = 0
    multikill_best: int = 0
    multikills: int = 0
    solo_kills: int = 0
    environmental_kills: int = 0
    environmental_deaths: int = 0
    critical_hits: int = 0
    critical_hit_accuracy: float = 0
    scoped_accuracy: float = 0
    scoped_critical_hit_accuracy: float = 0
    scoped_critical_hit_kills: int = 0
    shots_fired: int = 0
    shots_hit: int = 0
    shots_missed: int = 0
    scoped_shots_fired: int = 0
    scoped_shots_hit: int = 0
    weapon_accuracy: float = 0
    time_played: float = 0

    class Config:
        from_attributes = True


class MatchPlayerResponse(BaseModel):
    id: int
    player_name: str
    team_label: str
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    eliminations: int = 0
    final_blows: int = 0
    deaths: int = 0
    all_damage_dealt: float = 0
    hero_damage_dealt: float = 0
    healing_dealt: float = 0
    healing_received: float = 0
    self_healing: float = 0
    damage_taken: float = 0
    damage_blocked: float = 0
    defensive_assists: int = 0
    offensive_assists: int = 0
    objective_kills: int = 0
    ultimates_earned: int = 0
    ultimates_used: int = 0
    time_played: float = 0
    # Новые поля
    contribution_score: float = 0
    is_mvp: bool = False
    is_svp: bool = False
    last_hero: Optional[str] = None
    heroes: List[MatchPlayerHeroResponse] = []

    class Config:
        from_attributes = True


class MatchDetailResponse(BaseModel):
    id: int
    encounter_id: int
    tournament_id: int
    map_name: str
    game_mode: Optional[str] = None
    duration_seconds: Optional[float] = None
    map_number: Optional[int] = None
    winner_team_id: Optional[int] = None
    file_name: Optional[str] = None
    created_at: datetime
    team1: Optional[TeamResponse] = None
    team2: Optional[TeamResponse] = None
    players: List[MatchPlayerResponse] = []
    round_stats: Optional[list] = None

    class Config:
        from_attributes = True


class PlayerMappingItem(BaseModel):
    player_name: str
    user_id: int


class UploadLogRequest(BaseModel):
    encounter_id: int
    map_number: Optional[int] = None
    player_mappings: Optional[List[PlayerMappingItem]] = []


class KillFeedAssistItem(BaseModel):
    player_name: str
    team_label: str
    hero_name: str

    class Config:
        from_attributes = True


class KillFeedItem(BaseModel):
    id: int
    killer_name: str
    killer_team_label: str
    killer_hero: Optional[str] = None
    killer_user_id: Optional[int] = None
    victim_name: str
    victim_team_label: str
    victim_hero: Optional[str] = None
    victim_user_id: Optional[int] = None
    weapon: Optional[str] = None
    damage: float = 0
    is_critical: bool = False
    is_headshot: bool = False
    is_first_blood: bool = False
    timestamp: float
    round_number: int = 0
    offensive_assists: List[KillFeedAssistItem] = []
    defensive_assists: List[KillFeedAssistItem] = []

    class Config:
        from_attributes = True


class PlayerMatchHistoryItem(BaseModel):
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
    eliminations: int = 0
    final_blows: int = 0
    deaths: int = 0
    hero_damage_dealt: float = 0
    healing_dealt: float = 0
    damage_blocked: float = 0
    objective_kills: int = 0
    heroes: List[str] = []

    class Config:
        from_attributes = True


class FirstBloodItem(BaseModel):
    round_number: int
    killer_name: str
    killer_team_label: str
    killer_hero: Optional[str] = None
    killer_user_id: Optional[int] = None
    victim_name: str
    victim_team_label: str
    victim_hero: Optional[str] = None
    victim_user_id: Optional[int] = None
    weapon: Optional[str] = None
    timestamp: float

    class Config:
        from_attributes = True


EncounterResponse.model_rebuild()