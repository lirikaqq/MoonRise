"""add is_captain to tournament_participants

Revision ID: 011_add_is_captain
Revises: 010_stages_and_groups
Create Date: 2026-04-13

Добавляет флаг is_captain в TournamentParticipant для определения
кто будет формировать команду в драфте.
"""
from alembic import op
import sqlalchemy as sa

revision = '011_add_is_captain'
down_revision = '010_stages_and_groups'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'tournament_participants',
        sa.Column('is_captain', sa.Boolean(), server_default='false', nullable=False)
    )


def downgrade() -> None:
    op.drop_column('tournament_participants', 'is_captain')
