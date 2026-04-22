"""add tournament structure fields

Revision ID: 006_tournament_structure
Revises: a1b2c3d4e5f7
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_tournament_structure'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём ENUM тип structure_type
    structure_type_enum = sa.Enum(
        'SINGLE_ELIMINATION',
        'DOUBLE_ELIMINATION',
        'ROUND_ROBIN',
        'GROUPS_PLUS_PLAYOFF',
        'SWISS',
        name='structure_type',
        native_enum=True,
        create_constraint=True
    )
    structure_type_enum.create(op.get_bind(), checkfirst=True)

    # Добавляем колонку structure_type с дефолтом SINGLE_ELIMINATION
    op.add_column('tournaments', sa.Column('structure_type', structure_type_enum, nullable=False, server_default='SINGLE_ELIMINATION'))

    # Добавляем колонку structure_settings (JSON)
    op.add_column('tournaments', sa.Column('structure_settings', sa.JSON, nullable=True))

    # Добавляем колонку twitch_channel
    op.add_column('tournaments', sa.Column('twitch_channel', sa.String(100), nullable=True))


def downgrade() -> None:
    # Удаляем колонки
    op.drop_column('tournaments', 'twitch_channel')
    op.drop_column('tournaments', 'structure_settings')
    op.drop_column('tournaments', 'structure_type')

    # Удаляем ENUM тип
    structure_type_enum = sa.Enum(
        'SINGLE_ELIMINATION',
        'DOUBLE_ELIMINATION',
        'ROUND_ROBIN',
        'GROUPS_PLUS_PLAYOFF',
        'SWISS',
        name='structure_type',
        native_enum=True,
        create_constraint=True
    )
    structure_type_enum.drop(op.get_bind(), checkfirst=True)
