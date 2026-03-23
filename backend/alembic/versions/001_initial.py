"""Initial: users and battletags tables

Revision ID: 001
Revises: 
Create Date: 2026-03-23 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('discord_id'),
    )
    op.create_index(op.f('ix_users_discord_id'), 'users', ['discord_id'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create battletags table
    op.create_table(
        'battletags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(100), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_battletags_id'), 'battletags', ['id'], unique=False)
    op.create_index(op.f('ix_battletags_user_id'), 'battletags', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_battletags_user_id'), table_name='battletags')
    op.drop_index(op.f('ix_battletags_id'), table_name='battletags')
    op.drop_table('battletags')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_discord_id'), table_name='users')
    op.drop_table('users')