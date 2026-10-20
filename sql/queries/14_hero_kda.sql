-- 14. Средние убийства, смерти и помощь у ходовых героев.
-- Только герои с games >= 420; средние — round(avg(x), 2) по numeric, два знака.
--
-- Колонки: hero, games, avg_kills, avg_deaths, avg_assists
-- Порядок: avg_kills (округлённое) по убыванию, при равенстве hero по возрастанию
-- Строк:   29

SELECT
    h.name hero,
    COUNT(*) games,
    ROUND(AVG(mp.kills), 2) avg_kills,
    ROUND(AVG(mp.deaths), 2) avg_deaths,
    ROUND(AVG(mp.assists), 2) avg_assists
FROM heroes h
JOIN match_players mp USING (hero_id)
GROUP BY h.hero_id
HAVING COUNT(*) >= 420
ORDER BY avg_kills DESC, hero;

