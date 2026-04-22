from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import enum


class StageFormat(str, enum.Enum):
    """Формат этапа турнира."""
    ROUND_ROBIN = "ROUND_ROBIN"
    SWISS = "SWISS"
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"
    DOUBLE_ELIMINATION = "DOUBLE_ELIMINATION"


class SeedingRule(str, enum.Enum):
    """Правило распределения участников при переходе между этапами."""
    CROSS_GROUP_SEEDING = "CROSS_GROUP_SEEDING"  # A1 vs B2, B1 vs A2
    UPPER_LOWER_SPLIT = "UPPER_LOWER_SPLIT"  # Топ-N в верхнюю, остальные в нижнюю


class TournamentStage(Base):
    """Этап турнира (групповой, плей-офф и т.д.)"""
    __tablename__ = "tournament_stages"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_number = Column(Integer, nullable=False)  # Порядок этапа (1, 2, 3...)
    name = Column(String(100), nullable=False)  # Название этапа ("Групповой этап", "Плей-офф")

    format = Column(SAEnum(StageFormat, name="stage_format", create_constraint=True, native_enum=True), nullable=False)

    # Настройки этапа
    # {
    #   "stage_config": {
    #     "tie_breaking_rules": ["wins", "head_to_head"],
    #     "points_per_win": 3,
    #     "points_per_draw": 1,
    #     "points_per_loss": 0
    #   },
    #   "advancement_config": {  # Существует только если есть следующий этап
    #     "participants_to_advance_per_group": 4,
    #     "seeding_rule": "UPPER_LOWER_SPLIT",
    #     "rule_params": {
    #       "upper_bracket_ranks": [1, 2],
    #       "lower_bracket_ranks": [3, 4]
    #     }
    #   }
    # }
    settings = Column(JSON, nullable=True, default=None)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Связи
    tournament = relationship("Tournament", back_populates="stages")
    groups = relationship("StageGroup", back_populates="stage", cascade="all, delete-orphan", order_by="StageGroup.name")
    encounters = relationship(
        "Encounter",
        back_populates=None,
        cascade="all, delete-orphan",
        overlaps="stage_ref",
    )

    def __repr__(self):
        return f"<TournamentStage(id={self.id}, tournament={self.tournament_id}, stage={self.stage_number}, name={self.name}, format={self.format})>"


class StageGroup(Base):
    """Группа в рамках этапа турнира (для Round Robin, группового этапа)"""
    __tablename__ = "stage_groups"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("tournament_stages.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # "Группа A", "Группа B"

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Связи
    stage = relationship("TournamentStage", back_populates="groups")
    participants = relationship("TournamentParticipant", back_populates="group")

    def __repr__(self):
        return f"<StageGroup(id={self.id}, stage={self.stage_id}, name={self.name})>"
