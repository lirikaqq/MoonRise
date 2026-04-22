"""add team_config and division to tournaments

Revision ID: 003_add_team_config_and_division
Revises: 002_div_teams
Create Date: 2025-04-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '003_add_team_config_and_division'
down_revision = '002_div_teams'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем team_config с дефолтным пустым объектом
    op.add_column(
        'tournaments',
        sa.Column(
            'team_config',
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
        )
    )
    
    # Добавляем division (nullable, как мы и договаривались)
    op.add_column(
        'tournaments',
        sa.Column('division', sa.Integer(), nullable=True)
    )


def downgrade():
    op.drop_column('tournaments', 'division')
    op.drop_column('tournaments', 'team_config')