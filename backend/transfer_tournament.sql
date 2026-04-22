-- Перенос матчей и статистики из MIX #2 (ID=10) в MIX #3 (ID=13)

BEGIN;

-- Маппинг команд по имени
CREATE TEMP TABLE team_map AS
SELECT old.id as old_id, new.id as new_id
FROM (SELECT id, name FROM teams WHERE tournament_id = 10) old
JOIN (SELECT id, name FROM teams WHERE tournament_id = 13) new ON old.name = new.name;

-- Маппинг встреч по stage + round_number
CREATE TEMP TABLE enc_map AS
SELECT e10.id as old_id, e13.id as new_id
FROM encounters e10
JOIN encounters e13 ON e10.stage = e13.stage 
  AND e10.round_number = e13.round_number
  AND e10.tournament_id = 10 AND e13.tournament_id = 13;

-- Вставка матчей
INSERT INTO matches (encounter_id, tournament_id, team1_id, team2_id, winner_team_id, map_name, game_mode, duration_seconds, file_hash, file_name, map_number, round_stats, created_at)
SELECT em.new_id, 13, tm1.new_id, tm2.new_id, tmw.new_id, m.map_name, m.game_mode, m.duration_seconds, m.file_hash, m.file_name, m.map_number, m.round_stats, m.created_at
FROM matches m
JOIN enc_map em ON m.encounter_id = em.old_id
JOIN team_map tm1 ON m.team1_id = tm1.old_id
JOIN team_map tm2 ON m.team2_id = tm2.old_id
LEFT JOIN team_map tmw ON m.winner_team_id = tmw.old_id
WHERE m.tournament_id = 10;

-- Вставка MatchPlayer
INSERT INTO match_players (match_id, user_id, player_name, team_label, team_id, eliminations, final_blows, deaths, all_damage_dealt, hero_damage_dealt, healing_dealt, healing_received, self_healing, damage_taken, damage_blocked, defensive_assists, offensive_assists, objective_kills, ultimates_earned, ultimates_used, time_played, contribution_score, is_mvp, is_svp, last_hero, created_at)
SELECT mn.id, mp.user_id, mp.player_name, mp.team_label, tm.new_id, mp.eliminations, mp.final_blows, mp.deaths, mp.all_damage_dealt, mp.hero_damage_dealt, mp.healing_dealt, mp.healing_received, mp.self_healing, mp.damage_taken, mp.damage_blocked, mp.defensive_assists, mp.offensive_assists, mp.objective_kills, mp.ultimates_earned, mp.ultimates_used, mp.time_played, mp.contribution_score, mp.is_mvp, mp.is_svp, mp.last_hero, mp.created_at
FROM match_players mp
JOIN matches mo ON mp.match_id = mo.id
JOIN matches mn ON mo.file_hash = mn.file_hash AND mn.tournament_id = 13
LEFT JOIN team_map tm ON mp.team_id = tm.old_id
WHERE mo.tournament_id = 10;

-- Вставка MatchPlayerHero
WITH mp_map AS (
    SELECT mpo.id as old_id, mpn.id as new_id
    FROM match_players mpo
    JOIN match_players mpn ON mpo.user_id = mpn.user_id AND mpo.player_name = mpn.player_name
    JOIN matches mo ON mpo.match_id = mo.id
    JOIN matches mn ON mpn.match_id = mn.id
    WHERE mo.tournament_id = 10 AND mn.tournament_id = 13 AND mo.file_hash = mn.file_hash
)
INSERT INTO match_player_heroes (match_player_id, hero_name, eliminations, final_blows, deaths, all_damage_dealt, barrier_damage_dealt, hero_damage_dealt, healing_dealt, healing_received, self_healing, damage_taken, damage_blocked, defensive_assists, offensive_assists, objective_kills, ultimates_earned, ultimates_used, multikill_best, multikills, solo_kills, environmental_kills, environmental_deaths, critical_hits, critical_hit_accuracy, scoped_accuracy, scoped_critical_hit_accuracy, scoped_critical_hit_kills, shots_fired, shots_hit, shots_missed, scoped_shots_fired, scoped_shots_hit, weapon_accuracy, time_played)
SELECT mpm.new_id, mph.hero_name, mph.eliminations, mph.final_blows, mph.deaths, mph.all_damage_dealt, mph.barrier_damage_dealt, mph.hero_damage_dealt, mph.healing_dealt, mph.healing_received, mph.self_healing, mph.damage_taken, mph.damage_blocked, mph.defensive_assists, mph.offensive_assists, mph.objective_kills, mph.ultimates_earned, mph.ultimates_used, mph.multikill_best, mph.multikills, mph.solo_kills, mph.environmental_kills, mph.environmental_deaths, mph.critical_hits, mph.critical_hit_accuracy, mph.scoped_accuracy, mph.scoped_critical_hit_accuracy, mph.scoped_critical_hit_kills, mph.shots_fired, mph.shots_hit, mph.shots_missed, mph.scoped_shots_fired, mph.scoped_shots_hit, mph.weapon_accuracy, mph.time_played
FROM match_player_heroes mph
JOIN mp_map mpm ON mph.match_player_id = mpm.old_id;

COMMIT;
