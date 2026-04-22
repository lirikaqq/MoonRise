"""
Pydantic schemas для этапов и групп турнира.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class StageFormatEnum(str, Enum):
    ROUND_ROBIN = "ROUND_ROBIN"
    SWISS = "SWISS"
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"
    DOUBLE_ELIMINATION = "DOUBLE_ELIMINATION"


class SeedingRuleEnum(str, Enum):
    CROSS_GROUP_SEEDING = "CROSS_GROUP_SEEDING"
    UPPER_LOWER_SPLIT = "UPPER_LOWER_SPLIT"


class StageConfig(BaseModel):
    """Настройки самого этапа."""
    tie_breaking_rules: Optional[List[str]] = None
    points_per_win: Optional[int] = 3
    points_per_draw: Optional[int] = 1
    points_per_loss: Optional[int] = 0


class AdvancementConfig(BaseModel):
    """Настройки перехода к следующему этапу."""
    participants_to_advance_per_group: Optional[int] = 4
    seeding_rule: Optional[SeedingRuleEnum] = None
    rule_params: Optional[Dict[str, Any]] = None
    # Для UPPER_LOWER_SPLIT
    upper_bracket_ranks: Optional[List[int]] = None
    lower_bracket_ranks: Optional[List[int]] = None


class StageSettings(BaseModel):
    """Полные настройки этапа."""
    stage_config: Optional[StageConfig] = None
    advancement_config: Optional[AdvancementConfig] = None


class TournamentStageBase(BaseModel):
    """Базовая схема этапа."""
    stage_number: int
    name: str
    format: StageFormatEnum
    settings: Optional[StageSettings] = None


class TournamentStageCreate(TournamentStageBase):
    """Схема для создания этапа."""
    tournament_id: int


class TournamentStageUpdate(BaseModel):
    """Схема для обновления этапа."""
    name: Optional[str] = None
    format: Optional[StageFormatEnum] = None
    settings: Optional[StageSettings] = None


class TournamentStageResponse(TournamentStageBase):
    """Схема ответа этапа."""
    id: int
    tournament_id: int
    created_at: datetime
    updated_at: datetime
    groups: List['StageGroupResponse'] = []

    class Config:
        from_attributes = True


class StageGroupBase(BaseModel):
    """Базовая схема группы."""
    name: str


class StageGroupCreate(StageGroupBase):
    """Схема для создания группы."""
    stage_id: int


class StageGroupUpdate(BaseModel):
    """Схема для обновления группы."""
    name: Optional[str] = None


class StageGroupResponse(StageGroupBase):
    """Схема ответа группы."""
    id: int
    stage_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StageAdvancementResult(BaseModel):
    """Результат продвижения к следующему этапу."""
    next_stage_id: int
    advanced_participants: int
    upper_bracket_count: int
    lower_bracket_count: int
    encounters_created: int


# Обновляем forward references
TournamentStageResponse.model_rebuild()
