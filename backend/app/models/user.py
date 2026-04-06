from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    """Модель пользователя (игрока) — привязана к Discord."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Сделано nullable=True, чтобы разрешить создание "ghost" профилей без Discord
    discord_id = Column(String(50), unique=True, nullable=True, index=True) 
    
    username = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    role = Column(String(50), default="player", nullable=False)
    division = Column(String(50), nullable=True)

    # Игровые роли Overwatch
    primary_role = Column(String(50), nullable=True)
    secondary_role = Column(String(50), nullable=True)
    
    # Поле для "призрачных" профилей, созданных скриптом
    is_ghost = Column(Boolean, default=False, nullable=False)

    # Профиль
    bio = Column(Text, nullable=True)

    is_banned = Column(Boolean, default=False, nullable=False)
    ban_reason = Column(String(500), nullable=True)
    ban_until = Column(DateTime(timezone=True), nullable=True)

    reputation_score = Column(Integer, default=0, nullable=False)

    # Все даты теперь "aware" с часовым поясом UTC
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Связи
    battletags = relationship("BattleTag", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, discord_id={self.discord_id}, username={self.username})>"


class BattleTag(Base):
    """Привязанные Battle.net аккаунты игрока."""
    __tablename__ = "battletags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="battletags")

    def __repr__(self):
        return f"<BattleTag(id={self.id}, user_id={self.user_id}, tag={self.tag})>"