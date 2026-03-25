from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moonrise"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Discord OAuth2
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = "http://localhost:8000/auth/discord/callback"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    # JWT
    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    
    # Overfast API
    OVERFAST_API_URL: str = "https://overfast-api.tekrop.fr"
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()