"""add next_encounter_id to encounters

Revision ID: 014_add_next_encounter_id
Revises: 013_add_team_id_participants
Create Date: 2026-04-13

Добавляет next_encounter_id в Encounter для автоматического
продвижения победителя в следующий раунд single-elimination сетки.
"""
from alembic import op
import sqlalchemy as sa

revision = '014_add_next_encounter_id'
down_revision = '013_add_team_id_participants'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'encounters',
        sa.Column('next_encounter_id', sa.Integer(), sa.ForeignKey('encounters.id', ondelete='SET NULL'), nullable=True)
    )
    # Индекс для быстрого поиска следующих матчей
    op.create_index('ix_encounters_next_encounter_id', 'encounters', ['next_encounter_id'])


def downgrade() -> None:
    op.drop_index('ix_encounters_next_encounter_id', 'encounters')
    op.drop_column('encounters', 'next_encounter_id')
