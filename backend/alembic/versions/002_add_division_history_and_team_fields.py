"""002: division history + team fields

Revision ID: 002_div_teams
Revises: b7d9e517864f
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa


revision = "002_div_teams"
down_revision = "b7d9e517864f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Таблица user_division_history уже существует
    # division уже преобразован в Integer в предыдущих попытках
    # Просто фиксируем текущую версию
    pass


def downgrade() -> None:
    pass