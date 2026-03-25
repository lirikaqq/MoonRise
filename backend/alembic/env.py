from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
from app.database import Base
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

config = context.config

# Берём DATABASE_URL из окружения
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL не установлена в .env файле")

# Для миграций нужен синхронный драйвер (без asyncpg)
sync_database_url = database_url.replace("+asyncpg", "")

# Устанавливаем в конфиг
config.set_main_option("sqlalchemy.url", sync_database_url)

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Миграции в режиме 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Миграции в режиме 'online'."""
    url = config.get_main_option("sqlalchemy.url")
    
    # Создаём синхронный engine для миграций
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
