"""merge heads and add new match fields

Revision ID: a1b2c3d4e5f7
Revises: abc123456789, fb083d5d1356
Create Date: 2026-04-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = ('abc123456789', 'fb083d5d1356')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MatchPlayer: новые поля
    op.add_column('match_players', sa.Column('contribution_score', sa.Float(), nullable=True, server_default='0'))
    op.add_column('match_players', sa.Column('is_mvp', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('match_players', sa.Column('is_svp', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('match_players', sa.Column('last_hero', sa.String(100), nullable=True))

    # MatchKill: first blood
    op.add_column('match_kills', sa.Column('is_first_blood', sa.Integer(), nullable=True, server_default='0'))

    # Encounter: авто-создание
    op.add_column('encounters', sa.Column('is_auto_created', sa.Integer(), nullable=True, server_default='0'))

    # Tournament: лимиты встреч
    op.add_column('tournaments', sa.Column('max_group_encounters', sa.Integer(), nullable=True))
    op.add_column('tournaments', sa.Column('max_playoff_encounters', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('tournaments', 'max_playoff_encounters')
    op.drop_column('tournaments', 'max_group_encounters')
    op.drop_column('encounters', 'is_auto_created')
    op.drop_column('match_kills', 'is_first_blood')
    op.drop_column('match_players', 'last_hero')
    op.drop_column('match_players', 'is_svp')
    op.drop_column('match_players', 'is_mvp')
    op.drop_column('match_players', 'contribution_score')
