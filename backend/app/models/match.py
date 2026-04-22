from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    captain_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(20), nullable=False, default="manual")
    is_confirmed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tournament = relationship("Tournament", back_populates="teams")
    captain = relationship("User", foreign_keys=[captain_user_id])
    encounters_as_team1 = relationship("Encounter", foreign_keys="Encounter.team1_id", back_populates="team1")
    encounters_as_team2 = relationship("Encounter", foreign_keys="Encounter.team2_id", back_populates="team2")

    # Связи с драфтом и участниками
    draft_picks = relationship("DraftPick", back_populates="team")
    tournament_participants = relationship("TournamentParticipant", back_populates="team")


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_id = Column(Integer, ForeignKey("tournament_stages.id", ondelete="SET NULL"), nullable=True, index=True)
    team1_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team1_score = Column(Integer, default=0, nullable=False)
    team2_score = Column(Integer, default=0, nullable=False)
    winner_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    stage_name = Column("stage", String(100), nullable=True)  # Старое поле (строка), переименовали для ясности
    round_number = Column(Integer, nullable=True)
    is_auto_created = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Связь с следующим матчем в сетке (для single-elimination)
    next_encounter_id = Column(Integer, ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    tournament = relationship("Tournament", back_populates="encounters")
    stage_ref = relationship("TournamentStage", back_populates=None, overlaps="encounters")
    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="encounters_as_team1")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="encounters_as_team2")
    winner = relationship("Team", foreign_keys=[winner_team_id])
    matches = relationship("Match", back_populates="encounter", cascade="all, delete-orphan")

    # Связи для продвижения по сетке
    next_encounter = relationship("Encounter", remote_side=[id], backref="previous_encounters", foreign_keys=[next_encounter_id])


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    team1_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    winner_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    map_name = Column(String(100), nullable=False)
    game_mode = Column(String(100), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    file_hash = Column(String(64), unique=True, nullable=False)
    file_name = Column(String(255), nullable=True)
    map_number = Column(Integer, nullable=True)
    round_stats = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    encounter = relationship("Encounter", back_populates="matches")
    tournament = relationship("Tournament")
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    winner = relationship("Team", foreign_keys=[winner_team_id])
    players = relationship("MatchPlayer", back_populates="match", cascade="all, delete-orphan")
    kills = relationship("MatchKill", back_populates="match", cascade="all, delete-orphan")


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    player_name = Column(String(255), nullable=False)
    team_label = Column(String(50), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    eliminations = Column(Integer, default=0)
    final_blows = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    all_damage_dealt = Column(Float, default=0)
    hero_damage_dealt = Column(Float, default=0)
    healing_dealt = Column(Float, default=0)
    healing_received = Column(Float, default=0)
    self_healing = Column(Float, default=0)
    damage_taken = Column(Float, default=0)
    damage_blocked = Column(Float, default=0)
    defensive_assists = Column(Integer, default=0)
    offensive_assists = Column(Integer, default=0)
    objective_kills = Column(Integer, default=0)
    ultimates_earned = Column(Integer, default=0)
    ultimates_used = Column(Integer, default=0)
    time_played = Column(Float, default=0)

    # Contribution Score — комплексная метрика вклада игрока
    contribution_score = Column(Float, default=0)
    # MVP/SVP — лучший игрок матча / лучший игрок проигравшей команды
    is_mvp = Column(Integer, default=0)
    is_svp = Column(Integer, default=0)
    # Последний герой игрока (по времени на карте)
    last_hero = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    match = relationship("Match", back_populates="players")
    user = relationship("User")
    team = relationship("Team")
    heroes = relationship("MatchPlayerHero", back_populates="match_player", cascade="all, delete-orphan")


class MatchPlayerHero(Base):
    __tablename__ = "match_player_heroes"

    id = Column(Integer, primary_key=True, index=True)
    match_player_id = Column(Integer, ForeignKey("match_players.id", ondelete="CASCADE"), nullable=False, index=True)
    hero_name = Column(String(100), nullable=False)

    eliminations = Column(Integer, default=0)
    final_blows = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    all_damage_dealt = Column(Float, default=0)
    barrier_damage_dealt = Column(Float, default=0)
    hero_damage_dealt = Column(Float, default=0)
    healing_dealt = Column(Float, default=0)
    healing_received = Column(Float, default=0)
    self_healing = Column(Float, default=0)
    damage_taken = Column(Float, default=0)
    damage_blocked = Column(Float, default=0)
    defensive_assists = Column(Integer, default=0)
    offensive_assists = Column(Integer, default=0)
    objective_kills = Column(Integer, default=0)
    ultimates_earned = Column(Integer, default=0)
    ultimates_used = Column(Integer, default=0)
    multikill_best = Column(Integer, default=0)
    multikills = Column(Integer, default=0)
    solo_kills = Column(Integer, default=0)
    environmental_kills = Column(Integer, default=0)
    environmental_deaths = Column(Integer, default=0)
    critical_hits = Column(Integer, default=0)
    critical_hit_accuracy = Column(Float, default=0)
    scoped_accuracy = Column(Float, default=0)
    scoped_critical_hit_accuracy = Column(Float, default=0)
    scoped_critical_hit_kills = Column(Integer, default=0)
    shots_fired = Column(Integer, default=0)
    shots_hit = Column(Integer, default=0)
    shots_missed = Column(Integer, default=0)
    scoped_shots_fired = Column(Integer, default=0)
    scoped_shots_hit = Column(Integer, default=0)
    weapon_accuracy = Column(Float, default=0)
    time_played = Column(Float, default=0)

    match_player = relationship("MatchPlayer", back_populates="heroes")


class MatchKill(Base):
    __tablename__ = "match_kills"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)

    # Killer
    killer_name = Column(String(255), nullable=False)
    killer_team_label = Column(String(50), nullable=False)
    killer_hero = Column(String(100), nullable=True)
    killer_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Victim
    victim_name = Column(String(255), nullable=False)
    victim_team_label = Column(String(50), nullable=False)
    victim_hero = Column(String(100), nullable=True)
    victim_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Kill details
    weapon = Column(String(100), nullable=True)  # "Primary Fire", "Ultimate", "Melee", "Ability 1", etc.
    damage = Column(Float, default=0)
    is_critical = Column(Integer, default=0)  # boolean as int
    is_headshot = Column(Integer, default=0)  # boolean as int
    timestamp = Column(Float, nullable=False)  # seconds from match start
    round_number = Column(Integer, default=0)

    # Assists
    offensive_assists = Column(JSON, nullable=True)  # [{"player_name": "...", "hero": "...", "team_label": "..."}]
    defensive_assists = Column(JSON, nullable=True)

    # First Blood — первый килл раунда
    is_first_blood = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    match = relationship("Match", back_populates="kills")
    killer_user = relationship("User", foreign_keys=[killer_user_id])
    victim_user = relationship("User", foreign_keys=[victim_user_id])