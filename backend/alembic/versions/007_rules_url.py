"""add rules_url to tournaments

Revision ID: 007_rules_url
Revises: 006_tournament_structure
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_rules_url'
down_revision = '006_tournament_structure'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tournaments', sa.Column('rules_url', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('tournaments', 'rules_url')
