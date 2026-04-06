"""add_application_system

Revision ID: f92285a819c1
Revises: 2d7c2cbc5e8c
Create Date: ...

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = 'f92285a819c1'
down_revision = '2d7c2cbc5e8c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Добавляем application_data (JSON)
    op.add_column(
        'tournament_participants',
        sa.Column('application_data', JSON, nullable=True)
    )

    # Добавляем updated_at
    op.add_column(
        'tournament_participants',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()')
        )
    )

    # Меняем дефолт для status на 'pending'
    op.alter_column(
        'tournament_participants',
        'status',
        existing_type=sa.String(50),
        server_default='pending',
        nullable=False
    )

def downgrade() -> None:
    # Возвращаем дефолт для status
    op.alter_column(
        'tournament_participants',
        'status',
        existing_type=sa.String(50),
        server_default='registered',
        nullable=False
    )

    # Удаляем колонки
    op.drop_column('tournament_participants', 'updated_at')
    op.drop_column('tournament_participants', 'application_data')