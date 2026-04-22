"""add tournament stages and stage groups

Revision ID: 010_stages_and_groups
Revises: 009_homepage_twitch
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_stages_and_groups'
down_revision = '009_homepage_twitch'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу tournament_stages через raw SQL (enum уже существует)
    op.execute("""
        CREATE TABLE tournament_stages (
            id SERIAL PRIMARY KEY,
            tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
            stage_number INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            format stage_format NOT NULL,
            settings JSON,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    
    op.execute("""
        CREATE INDEX ix_tournament_stages_tournament_id ON tournament_stages(tournament_id)
    """)

    # Создаем таблицу stage_groups
    op.execute("""
        CREATE TABLE stage_groups (
            id SERIAL PRIMARY KEY,
            stage_id INTEGER NOT NULL REFERENCES tournament_stages(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    
    op.execute("""
        CREATE INDEX ix_stage_groups_stage_id ON stage_groups(stage_id)
    """)

    # Добавляем колонки в tournament_participants
    op.execute("""
        ALTER TABLE tournament_participants
        ADD COLUMN group_id INTEGER REFERENCES stage_groups(id) ON DELETE SET NULL
    """)
    
    op.execute("""
        ALTER TABLE tournament_participants
        ADD COLUMN seed INTEGER
    """)
    
    op.execute("""
        CREATE INDEX ix_tournament_participants_group_id ON tournament_participants(group_id)
    """)

    # Добавляем колонку в encounters
    op.execute("""
        ALTER TABLE encounters
        ADD COLUMN stage_id INTEGER REFERENCES tournament_stages(id) ON DELETE SET NULL
    """)
    
    op.execute("""
        CREATE INDEX ix_encounters_stage_id ON encounters(stage_id)
    """)


def downgrade() -> None:
    # Удаляем индексы
    op.execute("DROP INDEX IF EXISTS ix_encounters_stage_id")
    op.execute("DROP INDEX IF EXISTS ix_tournament_participants_group_id")
    op.execute("DROP INDEX IF EXISTS ix_stage_groups_stage_id")
    op.execute("DROP INDEX IF EXISTS ix_tournament_stages_tournament_id")

    # Удаляем колонки
    op.execute("ALTER TABLE encounters DROP COLUMN IF EXISTS stage_id")
    op.execute("ALTER TABLE tournament_participants DROP COLUMN IF EXISTS seed")
    op.execute("ALTER TABLE tournament_participants DROP COLUMN IF EXISTS group_id")

    # Удаляем таблицы
    op.execute("DROP TABLE IF EXISTS stage_groups")
    op.execute("DROP TABLE IF EXISTS tournament_stages")
