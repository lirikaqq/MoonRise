"""fix uq_team_active_captain and player_replacement nullable

Revision ID: 9fdff8242416
Revises: 0b74e805715b
Create Date: 2026-04-22 12:23:52.294529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9fdff8242416'
down_revision: Union[str, None] = '0b74e805715b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix 5v5 captain uniqueness + make PlayerReplacement.replaced_by_user_id nullable.

    We intentionally keep this migration minimal and safe (no unrelated type/default changes).
    """

    # 1) tournament_participants: replace legacy unique constraint
    # uq_team_active_captain (team_id, is_captain, is_active)
    # with partial unique index allowing many active non-captains.
    op.drop_constraint('uq_team_active_captain', 'tournament_participants', type_='unique')
    op.create_index(
        'uq_team_active_captain',
        'tournament_participants',
        ['team_id'],
        unique=True,
        postgresql_where=sa.text('is_captain IS true AND is_active IS true'),
    )

    # 2) player_replacements: allow history to survive deletion of admin/user
    op.alter_column(
        'player_replacements',
        'replaced_by_user_id',
        existing_type=sa.INTEGER(),
        nullable=True,
    )


def downgrade() -> None:
    # Best-effort rollback.
    # 1) tournament_participants
    op.drop_index(
        'uq_team_active_captain',
        table_name='tournament_participants',
        postgresql_where=sa.text('is_captain IS true AND is_active IS true'),
    )
    op.create_unique_constraint(
        'uq_team_active_captain',
        'tournament_participants',
        ['team_id', 'is_captain', 'is_active'],
    )

    # 2) player_replacements
    op.alter_column(
        'player_replacements',
        'replaced_by_user_id',
        existing_type=sa.INTEGER(),
        nullable=False,
    )
