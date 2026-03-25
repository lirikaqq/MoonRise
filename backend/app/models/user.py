from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """Модель пользователя (игрока) — привязана к Discord."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)

    # Профиль
    role = Column(String(50), default="player", nullable=False)  # player, moderator, admin
    division = Column(String(50), nullable=True)  # Gold, Silver, Bronze и т.д.

    # Статус
    is_banned = Column(Boolean, default=False, nullable=False)
    ban_reason = Column(String(500), nullable=True)
    ban_until = Column(DateTime, nullable=True)

    # Репутация (опционально)
    reputation_score = Column(Integer, default=0, nullable=False)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    battletags = relationship("BattleTag", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, discord_id={self.discord_id}, username={self.username})>"


class BattleTag(Base):
    """Привязанные Battle.net аккаунты игрока."""
    __tablename__ = "battletags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(100), nullable=False)  # например: Player#12345
    is_primary = Column(Boolean, default=False, nullable=False)  # основной баттлтег

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связь обратно к User
    user = relationship("User", back_populates="battletags")

    def __repr__(self):
        return f"<BattleTag(id={self.id}, user_id={self.user_id}, tag={self.tag})>"