-- 09. Кто из стримеров за какую команду выступает сейчас.
-- Только действующие составы; стримеры без player_id не выводятся.
--
-- Колонки: streamer, platform, player, team, tag, followers
-- Порядок: followers по убыванию, при равенстве streamer по возрастанию
-- Строк:   16

SELECT
    s.nickname streamer,
    pl.name platform,
    p.nickname player,
    t.name team,
    t.tag,
    s.followers
FROM streamers s
JOIN platforms pl USING (platform_id)
JOIN players p USING (player_id)
JOIN team_members tm ON tm.player_id = p.player_id AND tm.left_at IS NULL
JOIN teams t USING (team_id)
ORDER BY s.followers DESC, streamer;

