-- 18. Призовые турниров, до которых добрались игроки команды.
-- Турнир в зачёт один раз, если игрок сыграл его матч в составе: joined_at <=
-- started_at::date < left_at (пустой left_at — сейчас); команды без турниров не выводятся.
--
-- Колонки: team, tag, tournaments, prize_total
-- Порядок: prize_total по убыванию, при равенстве team по возрастанию
-- Строк:   22

WITH team_tournaments AS (
    SELECT DISTINCT tm.team_id, m.tournament_id
    FROM team_members tm
    JOIN match_players mp USING (player_id)
    JOIN matches m USING (match_id)
    WHERE m.tournament_id IS NOT NULL
        AND tm.joined_at <= m.started_at
        AND (tm.left_at IS NULL OR m.started_at < tm.left_at)
)
SELECT
    t.name team,
    t.tag tag,
    COUNT(*) tournaments,
    SUM(tr.prize_pool) prize_total
FROM team_tournaments tt
JOIN teams t USING (team_id)
JOIN tournaments tr USING (tournament_id)
GROUP BY t.team_id
ORDER BY prize_total DESC, team;

