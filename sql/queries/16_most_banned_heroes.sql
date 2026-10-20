-- 16. Десятка самых банимых героев.
-- bans — строки match_bans, picks — строки match_players, bans_per_pick =
-- round(bans::numeric / picks, 2); первые десять берутся после сортировки.
--
-- Колонки: hero, bans, picks, bans_per_pick
-- Порядок: bans по убыванию, при равенстве hero по возрастанию
-- Строк:   10

WITH bans AS (
    SELECT hero_id, COUNT(*) bans
    FROM match_bans
    GROUP BY hero_id
), picks AS (
    SELECT hero_id, COUNT(*) picks
    FROM match_players
    GROUP BY hero_id
)
SELECT
    h.name hero,
    b.bans bans,
    p.picks picks,
    ROUND(b.bans::numeric / p.picks, 2) bans_per_pick
FROM heroes AS h
JOIN bans AS b USING (hero_id)
JOIN picks AS p USING (hero_id)
ORDER BY b.bans DESC, hero
LIMIT 10;

