from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime
from app.database import Base


class HomepageSettings(Base):
    """Настройки блока Upcoming Tournament на главной."""
    __tablename__ = "homepage_settings"

    id = Column(Integer, primary_key=True, default=1)
    
    # Привязка к турниру (опционально)
    tournament_id = Column(Integer, nullable=True)
    
    # Контент блока
    title = Column(String(255), nullable=False, default="UPCOMING TOURNAMENT")
    date_text = Column(String(100), nullable=False, default="08 - 09 MARCH")
    description = Column(Text, nullable=False, default="")
    
    # Картинки
    logo_url = Column(String(500), nullable=True)
    hero_image_url = Column(String(500), nullable=True)
    
    # Кнопки
    registration_text = Column(String(100), default="REGISTRATION")
    registration_url = Column(String(500), default="#")
    info_text = Column(String(100), default="INFO")
    info_url = Column(String(500), default="#")

    # Twitch-канал для embed на главной
    twitch_channel = Column(String(100), nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)