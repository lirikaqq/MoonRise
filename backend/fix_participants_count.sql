-- Исправляет participants_count для всех турниров
-- Запускается один раз для синхронизации существующих данных

UPDATE tournaments
SET participants_count = (
    SELECT COUNT(*)
    FROM tournament_participants
    WHERE tournament_participants.tournament_id = tournaments.id
      AND tournament_participants.status = 'registered'
);

-- Проверка результата
SELECT id, title, participants_count,
    (SELECT COUNT(*) FROM tournament_participants 
     WHERE tournament_participants.tournament_id = tournaments.id 
     AND status = 'registered') as actual_count
FROM tournaments
ORDER BY id;
