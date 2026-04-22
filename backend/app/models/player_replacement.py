# app/models/player_replacement.py
from sqlalchemy import ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from .tournament import Tournament
    from .match import Team           # ← важно: файл называется match.py
    from .tournament import TournamentParticipant
    from .user import User


class PlayerReplacement(Base):
    """История замен игроков в турнире."""
    __tablename__ = "player_replacements"

    id: Mapped[int] = mapped_column(primary_key=True)

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    old_participant_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_participants.id", ondelete="CASCADE"), 
        nullable=False
    )

    new_participant_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_participants.id", ondelete="CASCADE"), 
        nullable=False
    )
    replaced_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )

    replaced_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_is_captain: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Relationships
    tournament: Mapped["Tournament"] = relationship("Tournament")
    team: Mapped["Team"] = relationship("Team")
    
    old_participant: Mapped["TournamentParticipant"] = relationship(
        "TournamentParticipant",
        foreign_keys=[old_participant_id],
        back_populates="replacements_as_old"
    )
    new_participant: Mapped["TournamentParticipant"] = relationship(
        "TournamentParticipant",
        foreign_keys=[new_participant_id],
        back_populates="replacements_as_new"
    )
    
    replaced_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[replaced_by_user_id]
    )

    __table_args__ = (
        Index("ix_player_replacements_tournament_team", "tournament_id", "team_id"),
        Index("ix_player_replacements_replaced_at", "replaced_at"),
    )

    def __repr__(self):
        return f"<PlayerReplacement(id={self.id}, old={self.old_participant_id}→new={self.new_participant_id})>"