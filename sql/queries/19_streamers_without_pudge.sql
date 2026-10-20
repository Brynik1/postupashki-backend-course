-- 19. Стримеры, которые ни разу не брали Pudge.
-- Только стримеры с непустым player_id и без единой игры за 'Pudge'; team — тег
-- команды с left_at IS NULL, иначе пусто; games — все строки match_players игрока.
--
-- Колонки: streamer, platform, team, followers, games
-- Порядок: followers по убыванию, при равенстве streamer по возрастанию
-- Строк:   8

SELECT
    s.nickname streamer,
    pl.name platform,
    t.tag team,
    s.followers followers,
    (SELECT COUNT(*) FROM match_players AS mp WHERE mp.player_id = s.player_id) games
FROM streamers s
JOIN platforms pl USING (platform_id)
LEFT JOIN team_members tm ON tm.player_id = s.player_id AND tm.left_at IS NULL
LEFT JOIN teams t USING (team_id)
WHERE s.player_id IS NOT NULL AND NOT EXISTS (
    SELECT 1
    FROM match_players mp
    JOIN heroes h USING (hero_id)
    WHERE mp.player_id = s.player_id AND h.name = 'Pudge'
)
ORDER BY s.followers DESC, streamer;

