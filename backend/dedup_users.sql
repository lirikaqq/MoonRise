-- Удаление дубликатов ghost-пользователей, перепривязка данных

BEGIN;

-- Создаём таблицу маппинга: старый ID → новый ID (минимальный ID для каждого username)
CREATE TEMP TABLE user_dedup AS
SELECT u.id as old_id, first.id as new_id, u.username
FROM users u
JOIN (
    SELECT username, min(id) as id
    FROM users
    GROUP BY username
    HAVING count(*) > 1
) first ON u.username = first.username
WHERE u.id != first.id;

-- Перепривязка match_players
UPDATE match_players
SET user_id = m.new_id
FROM user_dedup m
WHERE match_players.user_id = m.old_id;

-- Перепривязка match_kills (killer_user_id, victim_user_id)
UPDATE match_kills
SET killer_user_id = m.new_id
FROM user_dedup m
WHERE match_kills.killer_user_id = m.old_id;

UPDATE match_kills
SET victim_user_id = m.new_id
FROM user_dedup m
WHERE match_kills.victim_user_id = m.old_id;

-- Перепривязка tournament_participants
UPDATE tournament_participants
SET user_id = m.new_id
FROM user_dedup m
WHERE tournament_participants.user_id = m.old_id;

-- Перепривязка battletags
UPDATE battletags
SET user_id = m.new_id
FROM user_dedup m
WHERE battletags.user_id = m.old_id;

-- Удаляем дубликаты
DELETE FROM users WHERE id IN (SELECT old_id FROM user_dedup);

-- Удаляем пользователей без battletags и без match_players (чистые дубли без данных)
DELETE FROM users u
WHERE u.is_ghost = true
  AND u.id NOT IN (SELECT user_id FROM battletags)
  AND u.id NOT IN (SELECT user_id FROM match_players WHERE user_id IS NOT NULL)
  AND u.id NOT IN (SELECT user_id FROM tournament_participants);

-- Удаляем участников-дубликаты (если tournament_participants дублируется)
DELETE FROM tournament_participants
WHERE id NOT IN (
    SELECT min(id) FROM tournament_participants
    GROUP BY tournament_id, user_id
);

SELECT count(*) as deleted_users FROM user_dedup;
SELECT count(*) as remaining_dups FROM (SELECT username FROM users GROUP BY username HAVING count(*) > 1) x;

COMMIT;
