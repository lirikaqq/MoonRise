"""add player_replacements table and is_active column

Revision ID: 1afbbe49580f
Revises: fb083d5d1356
Create Date: 2026-04-21 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TEXT


revision = '1afbbe49580f'
down_revision = 'fb083d5d1356'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'tournament_participants',
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False)
    )

    op.create_table(
        'player_replacements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('old_participant_id', sa.Integer(), nullable=False),
        sa.Column('new_participant_id', sa.Integer(), nullable=False),
        sa.Column('replaced_by_user_id', sa.Integer(), nullable=False),
        sa.Column('replaced_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reason', TEXT(), nullable=True),
        sa.Column('previous_is_captain', sa.Boolean(), server_default='false', nullable=False),
        
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['old_participant_id'], ['tournament_participants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['new_participant_id'], ['tournament_participants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['replaced_by_user_id'], ['users.id'], ondelete='SET NULL'),
        
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_player_replacements_tournament_team', 'player_replacements', ['tournament_id', 'team_id'])
    op.create_index('ix_player_replacements_replaced_at', 'player_replacements', ['replaced_at'])

    op.create_unique_constraint(
        'uq_team_active_captain',
        'tournament_participants',
        ['team_id', 'is_captain', 'is_active']
    )


def downgrade():
    op.drop_constraint('uq_team_active_captain', 'tournament_participants', type_='unique')
    op.drop_index('ix_player_replacements_replaced_at', table_name='player_replacements')
    op.drop_index('ix_player_replacements_tournament_team', table_name='player_replacements')
    op.drop_table('player_replacements')
    op.drop_column('tournament_participants', 'is_active')