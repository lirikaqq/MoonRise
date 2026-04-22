"""add is_confirmed column to teams table

Revision ID: 005_add_is_confirmed_to_teams
Revises: fb083d5d1356
Create Date: 2025-04-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_is_confirmed_to_teams'
down_revision = 'fb083d5d1356'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'teams',
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade():
    op.drop_column('teams', 'is_confirmed')