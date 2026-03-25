"""add tournament participants

Revision ID: abc123participants
Revises: def456abc789
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123participants'
down_revision = 'def456abc789'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tournament_participants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tournament_id', sa.Integer(), sa.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='registered'),
        # registered, checkedin, disqualified
        sa.Column('registered_at', sa.DateTime(), nullable=False),
        sa.Column('checkedin_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_user'),
    )
    op.create_index('ix_tp_tournament_id', 'tournament_participants', ['tournament_id'])
    op.create_index('ix_tp_user_id', 'tournament_participants', ['user_id'])


def downgrade():
    op.drop_table('tournament_participants')