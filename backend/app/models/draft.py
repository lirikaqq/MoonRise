# app/models/draft.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DraftSession(Base):
    __tablename__ = "draft_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Статусы: pending (ждет старта), in_progress (идет), paused (пауза), completed (завершен)
    status = Column(String, default="pending", nullable=False)
    
    # Настройки
    pick_time_seconds = Column(Integer, default=90, nullable=False)
    team_size = Column(Integer, default=4, nullable=False) 
    
    # Состояние
    current_pick_index = Column(Integer, default=0, nullable=False) # Индекс в змейке (чей сейчас ход)
    pick_order = Column(JSON, nullable=False) # Массив ID: [1, 3, 5, 5, 3, 1]
    role_slots = Column(JSON, nullable=False) # Лимиты: {"tank": 1, "dps": 2, "support": 2}
    
    # Таймер
    current_pick_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Метки времени
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Связи (обрати внимание на имена связей)
    tournament = relationship("Tournament")
    captains = relationship("DraftCaptain", back_populates="session", cascade="all, delete-orphan")
    picks = relationship("DraftPick", back_populates="session", cascade="all, delete-orphan")
   

class DraftCaptain(Base):
    __tablename__ = "draft_captains"

    id = Column(Integer, primary_key=True, index=True)
    draft_session_id = Column(Integer, ForeignKey("draft_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    team_name = Column(String, nullable=False)
    pick_position = Column(Integer, nullable=False) # 1, 2, 3... (начальная позиция)
    captain_role = Column(String, nullable=True) # tank, dps, support (какую роль в команде занимает сам капитан)

    # Связи
    session = relationship("DraftSession", back_populates="captains")
    user = relationship("User")
    picks = relationship("DraftPick", back_populates="captain", cascade="all, delete-orphan")


class DraftPick(Base):
    __tablename__ = "draft_picks"

    id = Column(Integer, primary_key=True, index=True)
    draft_session_id = Column(Integer, ForeignKey("draft_sessions.id", ondelete="CASCADE"), nullable=False)
    captain_id = Column(Integer, ForeignKey("draft_captains.id", ondelete="CASCADE"), nullable=False)
    picked_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    pick_number = Column(Integer, nullable=False) # Глобальный номер пика (1, 2, 3...)
    round_number = Column(Integer, nullable=False) # Раунд (1, 2, 3...)
    assigned_role = Column(String, nullable=False) # tank, dps, support
    
    is_auto_pick = Column(Boolean, default=False, nullable=False)
    picked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    session = relationship("DraftSession", back_populates="picks")
    captain = relationship("DraftCaptain", back_populates="picks")
    picked_user = relationship("User")