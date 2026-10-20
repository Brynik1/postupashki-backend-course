-- 22. Стримеры с подписчиками выше среднего по своей площадке.
-- Строго больше среднего по всем стримерам площадки, сам стример в среднее входит;
-- platform_avg до 2 знаков; team — тег действующей команды, иначе NULL.
--
-- Колонки: streamer, platform, followers, platform_avg, team
-- Порядок: followers по убыванию, при равенстве streamer по возрастанию
-- Строк:   16

WITH platform_averages AS (
    SELECT platform_id, AVG(followers) platform_avg
    FROM streamers
    GROUP BY platform_id
)
SELECT
    s.nickname streamer,
    pl.name platform,
    s.followers,
    ROUND(a.platform_avg, 2) platform_avg,
    t.tag team
FROM streamers s
JOIN platform_averages a USING (platform_id)
JOIN platforms pl USING (platform_id)
LEFT JOIN team_members tm ON tm.player_id = s.player_id AND tm.left_at IS NULL
LEFT JOIN teams t USING (team_id)
WHERE s.followers > a.platform_avg
ORDER BY s.followers DESC, streamer;

