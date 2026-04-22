"""merge heads after database cleanup

Revision ID: 0b74e805715b
Revises: 003_add_team_config_and_division, 004_add_source_to_teams, 1afbbe49580f, 270c3843d356, b7cac6d6cf3f
Create Date: 2026-04-22 11:34:32.469326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b74e805715b'
down_revision: Union[str, None] = ('003_add_team_config_and_division', '004_add_source_to_teams', '1afbbe49580f', '270c3843d356', 'b7cac6d6cf3f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
