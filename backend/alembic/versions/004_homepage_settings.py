"""add homepage settings

Revision ID: abc123homepage
Revises: abc123participants
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123homepage'
down_revision = 'abc123participants'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'homepage_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tournament_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(255), nullable=False, server_default='UPCOMING TOURNAMENT'),
        sa.Column('date_text', sa.String(100), nullable=False, server_default='08 - 09 MARCH'),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('hero_image_url', sa.String(500), nullable=True),
        sa.Column('registration_text', sa.String(100), server_default='REGISTRATION'),
        sa.Column('registration_url', sa.String(500), server_default='#'),
        sa.Column('info_text', sa.String(100), server_default='INFO'),
        sa.Column('info_url', sa.String(500), server_default='#'),
        sa.Column('updated_at', sa.DateTime()),
    )
    
    # Вставляем начальные данные
    op.execute("""
        INSERT INTO homepage_settings (id, title, date_text, description, logo_url, hero_image_url, registration_text, registration_url, info_text, info_url)
        VALUES (1, 'UPCOMING TOURNAMENT', '08 - 09 MARCH',
        'ТУРНИР, В КОТОРОМ КОМАНДЫ ФОРМИРУЮТСЯ С ПОМОЩЬЮ ИНСТРУМЕНТОВ ДЛЯ БАЛАНСА КОМАНД. ОСНОВНОЙ ПРИНЦИП ФОРМИРОВАНИЯ КОМАНД — БАЛАНС СРЕДНЕГО РЕЙТИНГА МЕЖДУ ВСЕМИ КОМАНДАМИ.',
        '/assets/images/tournament-mix-logo.png', '/assets/images/tournament-hero.png',
        'REGISTRATION', '#', 'INFO', '#')
    """)


def downgrade():
    op.drop_table('homepage_settings')