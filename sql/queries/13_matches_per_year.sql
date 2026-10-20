-- 13. Сколько матчей сыграно в каждом году.
-- Год из started_at; tournament_matches — матчи с непустым tournament_id, ноль допустим.
--
-- Колонки: year, matches, tournament_matches
-- Порядок: year по возрастанию
-- Строк:   10

SELECT
    EXTRACT(YEAR FROM started_at) AS year,
    COUNT(*) matches,
    COUNT(tournament_id) tournament_matches
FROM matches
GROUP BY year
ORDER BY year;

