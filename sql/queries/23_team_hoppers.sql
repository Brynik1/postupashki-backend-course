-- 23. Игроки, поигравшие больше чем за одну команду.
-- Считаются различные team_id по всем периодам, строго больше одного; current_team —
-- название команды с пустым left_at, current_team и streamer могут быть NULL.
--
-- Колонки: player, country, teams_count, current_team, streamer
-- Порядок: teams_count по убыванию, при равенстве player по возрастанию
-- Строк:   25

WITH team_counts AS (
    SELECT player_id, COUNT(DISTINCT team_id) teams_count
    FROM team_members
    GROUP BY player_id
    HAVING COUNT(DISTINCT team_id) > 1
)
SELECT
    p.nickname player,
    p.country,
    tc.teams_count,
    t.name current_team,
    s.nickname streamer
FROM team_counts tc
JOIN players p USING (player_id)
LEFT JOIN team_members tm ON tm.player_id = p.player_id AND tm.left_at IS NULL
LEFT JOIN teams t USING (team_id)
LEFT JOIN streamers s ON s.player_id = p.player_id
ORDER BY tc.teams_count DESC, player;

