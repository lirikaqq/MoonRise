from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os

# Читаем переменные окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://moonrise:moonrise_secret@localhost:5432/moonrise")

# Создаём async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Поставь True если хочешь видеть SQL-запросы в логах
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool,  # Важно для async
)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Базовый класс для моделей
Base = declarative_base()


# Зависимость для FastAPI
async def get_db():
    """Получить сессию БД для эндпоинта."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()