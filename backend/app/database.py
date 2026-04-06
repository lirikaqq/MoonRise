# backend/app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    """Зависимость для получения сессии БД."""
    async with async_session_maker() as session:
        yield session

async def init_db():
    """Создает таблицы, если их нет."""
    # Импорты лучше держать на уровне модулей, а не внутри функций,
    # чтобы избежать циклических зависимостей. Alembic справится сам.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)