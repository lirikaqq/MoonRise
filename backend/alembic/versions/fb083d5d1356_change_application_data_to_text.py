"""change_application_data_to_text



Revision ID: fb083d5d1356
Revises: f92285a819c1
Create Date: 2026-04-05 09:27:09.688379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb083d5d1356'
down_revision: Union[str, None] = 'f92285a819c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        'tournament_participants',
        'application_data',
        existing_type=sa.JSON,
        type_=sa.Text,
        existing_nullable=True
    )

def downgrade():
    op.alter_column(
        'tournament_participants',
        'application_data',
        existing_type=sa.Text,
        type_=sa.JSON,
        existing_nullable=True
    )