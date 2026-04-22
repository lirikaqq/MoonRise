"""fix tournament_participants self referential relationship

Revision ID: 270c3843d356
Revises: 005_add_is_confirmed_to_teams
Create Date: 2026-04-21 17:46:20.441910
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '270c3843d356'
down_revision = '005_add_is_confirmed_to_teams'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Мы уже вручную создали колонки и foreign key ранее.
    # Эта миграция нужна только чтобы Alembic понял текущее состояние базы.
    
    # Если constraint ещё не создан — создаём
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'fk_tournament_participants_replaced_by'
            ) THEN
                ALTER TABLE tournament_participants 
                ADD CONSTRAINT fk_tournament_participants_replaced_by 
                FOREIGN KEY (replaced_by) REFERENCES tournament_participants(id);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    # При откате ничего не удаляем, чтобы не потерять данные
    pass