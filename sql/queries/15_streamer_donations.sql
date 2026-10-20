-- 15. Сколько донатов собрал каждый стример.
-- В ответе все стримеры: без донатов donations = 0 и total_amount = 0.00;
-- team — команда с left_at IS NULL, иначе пусто.
--
-- Колонки: streamer, platform, team, donations, total_amount
-- Порядок: total_amount по убыванию, при равенстве streamer по возрастанию
-- Строк:   40

SELECT
    s.nickname streamer,
    pl.name platform,
    t.name team,
    COUNT(d.donation_id) donations,
    COALESCE(SUM(d.amount), 0.00) total_amount
FROM streamers s
JOIN platforms pl USING (platform_id)
LEFT JOIN team_members tm ON tm.player_id = s.player_id AND tm.left_at IS NULL
LEFT JOIN teams t USING (team_id)
LEFT JOIN streams st USING (streamer_id)
LEFT JOIN stream_donations d USING (stream_id)
GROUP BY s.streamer_id, pl.name, t.name
ORDER BY total_amount DESC, streamer;

