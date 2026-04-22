# backend/app/config.py
from pydantic_settings import BaseSettings
import warnings

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
    ENVIRONMENT: str = "development"  # development | production

    def model_post_init(self, __context):
        # Валидация SECRET_KEY
        if len(self.SECRET_KEY) < 32:
            warnings.warn(
                "SECRET_KEY слишком короткий! Рекомендуется минимум 32 символа для HS256.",
                UserWarning,
                stacklevel=2
            )

    class Config:
        env_file = ".env"

settings = Settings()