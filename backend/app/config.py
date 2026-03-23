from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Настройки приложения из .env"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://moonrise:moonrise_secret@localhost:5432/moonrise"
    
    # JWT
    JWT_SECRET: str = "your-super-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 дней
    
    # Discord OAuth2
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = "http://localhost:8000/auth/discord/callback"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    class Config:
        # Ищем .env в корне проекта (на уровень выше backend)
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        extra = "allow"


settings = Settings()