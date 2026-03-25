"""Initial: create users and battletags

Revision ID: abc1234def567
Revises: 
Create Date: 2026-03-24 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'abc1234def567'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discord_id', sa.String(50), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='player'),
        sa.Column('division', sa.String(50), nullable=True),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ban_reason', sa.String(500), nullable=True),
        sa.Column('ban_until', sa.DateTime(), nullable=True),
        sa.Column('reputation_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_discord_id', 'users', ['discord_id'], unique=True)
    
    op.create_table(
        'battletags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(100), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_battletags_user_id', 'battletags', ['user_id'])


def downgrade() -> None:
    op.drop_table('battletags')
    op.drop_table('users')