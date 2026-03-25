from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(String(50), nullable=False)
    cover_url = Column(String(500), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    registration_open = Column(DateTime, nullable=True)
    registration_close = Column(DateTime, nullable=True)
    checkin_open = Column(DateTime, nullable=True)
    checkin_close = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="upcoming")
    max_participants = Column(Integer, nullable=True, default=100)
    participants_count = Column(Integer, nullable=False, default=0)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связь с участниками
    participants = relationship("TournamentParticipant", back_populates="tournament", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tournament(id={self.id}, title={self.title})>"


class TournamentParticipant(Base):
    """Участник турнира."""
    __tablename__ = "tournament_participants"

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="registered")
    # registered, checkedin, disqualified
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    checkedin_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_user'),
    )

    # Связи
    tournament = relationship("Tournament", back_populates="participants")
    user = relationship("User")

    def __repr__(self):
        return f"<TournamentParticipant(tournament={self.tournament_id}, user={self.user_id})>"