from sqlalchemy import (
    String, Integer, DateTime, Text,
    ForeignKey, Boolean, Enum as SAEnum, JSON,
    Index, UniqueConstraint, and_
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from .player_replacement import PlayerReplacement
    from .match import Team, Encounter
    from .user import User
    from .tournament_stage import StageGroup, TournamentStage
    from .draft import DraftSession

import enum


class StructureType(str, enum.Enum):
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"
    DOUBLE_ELIMINATION = "DOUBLE_ELIMINATION"
    ROUND_ROBIN = "ROUND_ROBIN"
    GROUPS_PLUS_PLAYOFF = "GROUPS_PLUS_PLAYOFF"
    SWISS = "SWISS"


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    description_general: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_dates: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_open: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_close: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checkin_open: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checkin_close: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="upcoming")
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=100)
    participants_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    max_group_encounters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_playoff_encounters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    structure_type: Mapped[StructureType] = mapped_column(
        SAEnum(StructureType, name="structure_type", create_constraint=True, native_enum=True),
        nullable=False,
        default=StructureType.SINGLE_ELIMINATION
    )
    structure_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    twitch_channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rules_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_sheet_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    team_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    division: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ==================== RELATIONSHIPS (ИСПРАВЛЕНО) ====================
    
    participants: Mapped[List["TournamentParticipant"]] = relationship(
        "TournamentParticipant", 
        back_populates="tournament", 
        cascade="all, delete-orphan"
    )
    
    teams: Mapped[List["Team"]] = relationship(
        "Team", 
        back_populates="tournament", 
        cascade="all, delete-orphan"
    )
    
    # ← ДОБАВЛЕНО (этого не хватало!)
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter", 
        back_populates="tournament", 
        cascade="all, delete-orphan"
    )
    
    stages: Mapped[List["TournamentStage"]] = relationship(
        "TournamentStage", 
        back_populates="tournament", 
        cascade="all, delete-orphan"
    )
    
    # ← ДОБАВЛЕНО
    draft_session: Mapped[Optional["DraftSession"]] = relationship(
        "DraftSession", 
        back_populates="tournament", 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tournament(id={self.id}, title={self.title})>"


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id: Mapped[int] = mapped_column(primary_key=True)

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    application_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stage_groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    team_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    registered_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    checkedin_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    replaced_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "tournament_participants.id",
            name="fk_tournament_participants_replaced_by",
        ),
        nullable=True,
    )
    replaced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    tournament: Mapped["Tournament"] = relationship(
        "Tournament", back_populates="participants"
    )
    user: Mapped["User"] = relationship("User")
    group: Mapped[Optional["StageGroup"]] = relationship(
        "StageGroup", back_populates="participants"
    )
    team: Mapped[Optional["Team"]] = relationship(
        "Team", back_populates="tournament_participants"
    )

    replacements_as_old: Mapped[List["PlayerReplacement"]] = relationship(
        "PlayerReplacement",
        foreign_keys="PlayerReplacement.old_participant_id",
        back_populates="old_participant",
    )
    replacements_as_new: Mapped[List["PlayerReplacement"]] = relationship(
        "PlayerReplacement",
        foreign_keys="PlayerReplacement.new_participant_id",
        back_populates="new_participant",
    )

    __table_args__ = (
        UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_user'),
        # 5v5 rule: in one team only 1 active captain allowed.
        # We implement it as a partial unique index so multiple active non-captains are allowed.
        Index(
            'uq_team_active_captain',
            'team_id',
            unique=True,
            postgresql_where=and_(is_captain.is_(True), is_active.is_(True)),
        ),
    )

    def __repr__(self):
        return f"<TournamentParticipant(id={self.id}, active={self.is_active})>"