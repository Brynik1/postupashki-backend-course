-- 21. Турнирные выступления с KDA выше шестикратного среднего.
-- KDA = (kills + assists)::numeric / GREATEST(deaths, 1); порог — строго больше шести
-- средних KDA по всей match_players; только матчи турниров; kda округлить до 2 знаков.
--
-- Колонки: match_id, tournament, player, hero, kda
-- Порядок: kda по убыванию, при равенстве match_id, затем slot
-- Строк:   60

WITH performances AS (
    SELECT
        mp.*,
        (kills + assists)::numeric / GREATEST(deaths, 1) kda
    FROM match_players mp
)
SELECT
    mp.match_id,
    t.name tournament,
    p.nickname player,
    h.name hero,
    ROUND(mp.kda, 2) kda
FROM performances mp
JOIN matches m USING (match_id)
JOIN tournaments t USING (tournament_id)
JOIN players p USING (player_id)
JOIN heroes h USING (hero_id)
WHERE mp.kda > 6 * (SELECT AVG(kda) FROM performances)
ORDER BY kda DESC, mp.match_id, mp.slot;

