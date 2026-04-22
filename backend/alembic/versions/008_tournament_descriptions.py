"""replace description with 3 structured fields

Revision ID: 008_tournament_descriptions
Revises: 007_rules_url
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_tournament_descriptions'
down_revision = '007_rules_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем 3 новых поля
    op.add_column('tournaments', sa.Column('description_general', sa.Text, nullable=True))
    op.add_column('tournaments', sa.Column('description_dates', sa.Text, nullable=True))
    op.add_column('tournaments', sa.Column('description_requirements', sa.Text, nullable=True))

    # Мигрируем существующие данные из description в description_general
    op.execute("""
        UPDATE tournaments
        SET description_general = description
        WHERE description IS NOT NULL AND description != ''
    """)

    # Удаляем старую колонку description
    op.drop_column('tournaments', 'description')


def downgrade() -> None:
    # Восстанавливаем description
    op.add_column('tournaments', sa.Column('description', sa.Text, nullable=True))

    # Мигрируем данные обратно
    op.execute("""
        UPDATE tournaments
        SET description = description_general
        WHERE description_general IS NOT NULL AND description_general != ''
    """)

    # Удаляем новые поля
    op.drop_column('tournaments', 'description_requirements')
    op.drop_column('tournaments', 'description_dates')
    op.drop_column('tournaments', 'description_general')
