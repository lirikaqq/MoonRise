"""005_matches

Revision ID: 005matches
Revises: abc123homepage
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '005matches'
down_revision = 'abc123homepage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Таблица teams
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('captain_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['captain_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_teams_id', 'teams', ['id'])
    op.create_index('ix_teams_tournament_id', 'teams', ['tournament_id'])

    # Таблица encounters
    op.create_table(
        'encounters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('team1_id', sa.Integer(), nullable=False),
        sa.Column('team2_id', sa.Integer(), nullable=False),
        sa.Column('team1_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('team2_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winner_team_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(100), nullable=True),
        sa.Column('round_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team1_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team2_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['winner_team_id'], ['teams.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_encounters_id', 'encounters', ['id'])
    op.create_index('ix_encounters_tournament_id', 'encounters', ['tournament_id'])

    # Таблица matches
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('team1_id', sa.Integer(), nullable=False),
        sa.Column('team2_id', sa.Integer(), nullable=False),
        sa.Column('winner_team_id', sa.Integer(), nullable=True),
        sa.Column('map_name', sa.String(100), nullable=False),
        sa.Column('game_mode', sa.String(100), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('map_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team1_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team2_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['winner_team_id'], ['teams.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('file_hash', name='uq_matches_file_hash'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_matches_id', 'matches', ['id'])
    op.create_index('ix_matches_encounter_id', 'matches', ['encounter_id'])
    op.create_index('ix_matches_tournament_id', 'matches', ['tournament_id'])

    # Таблица match_players
    op.create_table(
        'match_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('player_name', sa.String(255), nullable=False),
        sa.Column('team_label', sa.String(50), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('kills', sa.Integer(), server_default='0'),
        sa.Column('deaths', sa.Integer(), server_default='0'),
        sa.Column('assists', sa.Integer(), server_default='0'),
        sa.Column('damage_dealt', sa.Float(), server_default='0'),
        sa.Column('damage_taken', sa.Float(), server_default='0'),
        sa.Column('healing_done', sa.Float(), server_default='0'),
        sa.Column('damage_blocked', sa.Float(), server_default='0'),
        sa.Column('time_played', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_match_players_id', 'match_players', ['id'])
    op.create_index('ix_match_players_match_id', 'match_players', ['match_id'])
    op.create_index('ix_match_players_user_id', 'match_players', ['user_id'])

    # Таблица match_player_heroes
    op.create_table(
        'match_player_heroes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_player_id', sa.Integer(), nullable=False),
        sa.Column('hero_name', sa.String(100), nullable=False),
        sa.Column('kills', sa.Integer(), server_default='0'),
        sa.Column('deaths', sa.Integer(), server_default='0'),
        sa.Column('assists', sa.Integer(), server_default='0'),
        sa.Column('damage_dealt', sa.Float(), server_default='0'),
        sa.Column('damage_taken', sa.Float(), server_default='0'),
        sa.Column('healing_done', sa.Float(), server_default='0'),
        sa.Column('damage_blocked', sa.Float(), server_default='0'),
        sa.Column('time_played', sa.Float(), server_default='0'),
        sa.ForeignKeyConstraint(['match_player_id'], ['match_players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_match_player_heroes_id', 'match_player_heroes', ['id'])
    op.create_index('ix_match_player_heroes_match_player_id', 'match_player_heroes', ['match_player_id'])


def downgrade() -> None:
    op.drop_table('match_player_heroes')
    op.drop_table('match_players')
    op.drop_table('matches')
    op.drop_table('encounters')
    op.drop_table('teams')