"""add team_id to draft_picks

Revision ID: 012_add_team_id_draft_picks
Revises: 011_add_is_captain
Create Date: 2026-04-13

Добавляет team_id в DraftPick для связи выбранных игроков
с созданными командами после завершения драфта.
"""
from alembic import op
import sqlalchemy as sa

revision = '012_add_team_id_draft_picks'
down_revision = '011_add_is_captain'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'draft_picks',
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('draft_picks', 'team_id')
