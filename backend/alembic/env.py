import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# Добавляем /app в path чтобы импорты работали
sys.path.insert(0, '/app')

# Импортируем все модели чтобы autogenerate их видел
from app.database import Base
from app.models.user import User, BattleTag
from app.models.tournament import Tournament, TournamentParticipant

# Попытаться импортировать остальные модели если они есть
try:
    from app.models.match import Encounter, Team
except ImportError:
    pass

# Alembic Config
config = context.config

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate
target_metadata = Base.metadata

# Берём DATABASE_URL из env (asyncpg)
def get_url():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://moonrise:moonrise@postgres:5432/moonrise"
    )
    return url

def run_migrations_offline() -> None:
    """Миграции без подключения к БД (генерирует SQL)"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,       # Замечает изменения типов колонок
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Миграции с реальным подключением к БД (asyncpg)"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

# Запуск
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())