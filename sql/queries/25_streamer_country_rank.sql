-- 25. Место стримера-профессионала в рейтинге своей страны.
-- Только стримеры с player_id и действующей записью в team_members; место по mmr
-- по убыванию и country_players считаются по всей players; player — ник из players.
--
-- Колонки: player, country, mmr, country_rank, country_players, team_tag, platform
-- Порядок: country по возрастанию, внутри страны country_rank по возрастанию
-- Строк:   16

WITH ranked_players AS (
    SELECT p.*,
           RANK() OVER (PARTITION BY country ORDER BY mmr DESC) AS country_rank,
           COUNT(*) OVER (PARTITION BY country) AS country_players
    FROM players AS p
)
SELECT p.nickname AS player, p.country, p.mmr, p.country_rank, p.country_players,
       t.tag AS team_tag, pl.name AS platform
FROM ranked_players AS p
JOIN streamers AS s USING (player_id)
JOIN team_members AS tm ON tm.player_id = p.player_id AND tm.left_at IS NULL
JOIN teams AS t USING (team_id)
JOIN platforms AS pl USING (platform_id)
ORDER BY p.country, p.country_rank;

