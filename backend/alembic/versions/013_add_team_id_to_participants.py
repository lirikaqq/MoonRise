"""add team_id to tournament_participants

Revision ID: 013_add_team_id_participants
Revises: 012_add_team_id_draft_picks
Create Date: 2026-04-13

Добавляет team_id в TournamentParticipant для связи участников
с командами после завершения драфта.
"""
from alembic import op
import sqlalchemy as sa

revision = '013_add_team_id_participants'
down_revision = '012_add_team_id_draft_picks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'tournament_participants',
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('tournament_participants', 'team_id')
