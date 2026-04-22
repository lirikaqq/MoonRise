"""add twitch_channel to homepage_settings

Revision ID: 009_homepage_twitch
Revises: 008_tournament_descriptions
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = '009_homepage_twitch'
down_revision = '008_tournament_descriptions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('homepage_settings', sa.Column('twitch_channel', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('homepage_settings', 'twitch_channel')
