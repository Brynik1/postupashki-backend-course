-- 24. Турниры, чей призовой фонд больше суммы призовых всех предыдущих.
-- Предыдущие — со строго меньшим started_at, сравнение строгое; у первого турнира
-- prev_total и prev_count нули, не NULL; matches_played — число матчей турнира.
--
-- Колонки: tournament, started_at, prize_pool, prev_total, prev_count, matches_played
-- Порядок: started_at по возрастанию
-- Строк:   2

WITH history AS (
    SELECT
        t.*,
        (
            SELECT COALESCE(SUM(prev.prize_pool), 0)
            FROM tournaments prev WHERE prev.started_at < t.started_at
        ) prev_total,
        (
            SELECT COUNT(*)
            FROM tournaments prev WHERE prev.started_at < t.started_at
        ) prev_count
    FROM tournaments t
)
SELECT
    h.name tournament,
    h.started_at,
    h.prize_pool,
    h.prev_total,
    h.prev_count,
    (
        SELECT COUNT(*)
        FROM matches m WHERE m.tournament_id = h.tournament_id
    ) matches_played
FROM history h
WHERE h.prize_pool > h.prev_total
ORDER BY h.started_at;

