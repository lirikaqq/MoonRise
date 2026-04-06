from sqlalchemy import Column, String, Integer, DateTime, Text, UniqueConstraint, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(String(50), nullable=False)
    cover_url = Column(String(500), nullable=True)
    
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    registration_open = Column(DateTime(timezone=True), nullable=True)
    registration_close = Column(DateTime(timezone=True), nullable=True)
    checkin_open = Column(DateTime(timezone=True), nullable=True)
    checkin_close = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(String(50), nullable=False, default="upcoming")
    max_participants = Column(Integer, nullable=True, default=100)
    participants_count = Column(Integer, nullable=False, default=0)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Связи (убедись, что имена моделей в relationship совпадают с твоими, например, 'DraftSession')
    # Если каких-то моделей у тебя еще нет, закомментируй соответствующую строку
    draft_session = relationship("DraftSession", back_populates="tournament", uselist=False, cascade="all, delete-orphan")
    participants = relationship("TournamentParticipant", back_populates="tournament", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="tournament", cascade="all, delete-orphan")
    encounters = relationship("Encounter", back_populates="tournament", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tournament(id={self.id}, title={self.title}, format={self.format})>"


class TournamentParticipant(Base):
    """Участник турнира / заявка на турнир."""
    __tablename__ = "tournament_participants"

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(50), nullable=False, default="pending")
    is_allowed = Column(Boolean, default=False, nullable=False)
    application_data = Column(Text, nullable=True)

    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    checkedin_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_user'),
    )

    tournament = relationship("Tournament", back_populates="participants")
    user = relationship("User")

    def __repr__(self):
        return f"<TournamentParticipant(tournament={self.tournament_id}, user={self.user_id}, status={self.status})>"