"""add source column to teams table

Revision ID: 004_add_source_to_teams
Revises: 002_div_teams
Create Date: 2025-04-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_source_to_teams'
down_revision = '002_div_teams'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'teams',
        sa.Column('source', sa.String(length=20), nullable=False, server_default='manual')
    )


def downgrade():
    op.drop_column('teams', 'source')