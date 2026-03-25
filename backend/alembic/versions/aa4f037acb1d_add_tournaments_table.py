"""Add tournaments table

Revision ID: def456abc789
Revises: abc1234def567
Create Date: 2026-03-24 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'def456abc789'
down_revision = 'abc1234def567'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tournaments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.String(50), nullable=False),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('registration_open', sa.DateTime(), nullable=True),
        sa.Column('registration_close', sa.DateTime(), nullable=True),
        sa.Column('checkin_open', sa.DateTime(), nullable=True),
        sa.Column('checkin_close', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='upcoming'),
        sa.Column('max_participants', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('participants_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tournaments_id', 'tournaments', ['id'])
    op.create_index('ix_tournaments_status', 'tournaments', ['status'])
    op.create_index('ix_tournaments_format', 'tournaments', ['format'])


def downgrade() -> None:
    op.drop_index('ix_tournaments_format', table_name='tournaments')
    op.drop_index('ix_tournaments_status', table_name='tournaments')
    op.drop_index('ix_tournaments_id', table_name='tournaments')
    op.drop_table('tournaments')