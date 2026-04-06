# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str
    FRONTEND_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    
    class Config:
        # Эта строка говорит, что нужно читать переменные из .env файла,
        # но переменные, установленные Docker'ом, будут иметь приоритет.
        env_file = ".env"
        
settings = Settings()