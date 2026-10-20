-- 20. Герои, которых на патче банили чаще, чем брали.
-- Патч — matches.patch_id; в ответе пары с bans строго больше picks, diff = bans - picks.
--
-- Колонки: version, hero, bans, picks, diff
-- Порядок: diff по убыванию, затем hero по возрастанию, затем version по возрастанию
-- Строк:   99

WITH bans AS (
    SELECT m.patch_id, b.hero_id, COUNT(*) bans
    FROM matches m
    JOIN match_bans b USING (match_id)
    GROUP BY m.patch_id, b.hero_id
), picks AS (
    SELECT m.patch_id, mp.hero_id, COUNT(*) picks
    FROM matches m
    JOIN match_players mp USING (match_id)
    GROUP BY m.patch_id, mp.hero_id
)
SELECT
    p.version,
    h.name hero,
    b.bans,
    COALESCE(pk.picks, 0) picks,
    b.bans - COALESCE(pk.picks, 0) diff
FROM bans  b
LEFT JOIN picks pk USING (patch_id, hero_id)
JOIN patches p USING (patch_id)
JOIN heroes h USING (hero_id)
WHERE b.bans > COALESCE(pk.picks, 0)
ORDER BY diff DESC, hero, p.version;

