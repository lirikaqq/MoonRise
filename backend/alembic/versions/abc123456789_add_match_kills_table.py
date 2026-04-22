"""add_match_kills_table

Revision ID: abc123456789
Revises: fb083d5d1356
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123456789'
down_revision: Union[str, None] = '5435a949a9fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('match_kills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('killer_name', sa.String(length=255), nullable=False),
        sa.Column('killer_team_label', sa.String(length=50), nullable=False),
        sa.Column('killer_hero', sa.String(length=100), nullable=True),
        sa.Column('killer_user_id', sa.Integer(), nullable=True),
        sa.Column('victim_name', sa.String(length=255), nullable=False),
        sa.Column('victim_team_label', sa.String(length=50), nullable=False),
        sa.Column('victim_hero', sa.String(length=100), nullable=True),
        sa.Column('victim_user_id', sa.Integer(), nullable=True),
        sa.Column('weapon', sa.String(length=100), nullable=True),
        sa.Column('damage', sa.Float(), nullable=True),
        sa.Column('is_critical', sa.Integer(), nullable=True),
        sa.Column('is_headshot', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=True),
        sa.Column('offensive_assists', sa.JSON(), nullable=True),
        sa.Column('defensive_assists', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['killer_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['victim_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_kills_id'), 'match_kills', ['id'], unique=False)
    op.create_index(op.f('ix_match_kills_match_id'), 'match_kills', ['match_id'], unique=False)
    op.create_index(op.f('ix_match_kills_killer_user_id'), 'match_kills', ['killer_user_id'], unique=False)
    op.create_index(op.f('ix_match_kills_victim_user_id'), 'match_kills', ['victim_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_match_kills_victim_user_id'), table_name='match_kills')
    op.drop_index(op.f('ix_match_kills_killer_user_id'), table_name='match_kills')
    op.drop_index(op.f('ix_match_kills_match_id'), table_name='match_kills')
    op.drop_index(op.f('ix_match_kills_id'), table_name='match_kills')
    op.drop_table('match_kills')
