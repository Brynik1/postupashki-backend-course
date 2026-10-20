-- 08. Сколько в команде игроков и сколько среди них стримеров.
-- Считаются только незакрытые периоды; команда без состава остаётся
-- в ответе с нулями, стримеры без player_id не учитываются.
--
-- Колонки: name, tag, players_now, streamers_now
-- Порядок: players_now по убыванию, при равенстве name по возрастанию
-- Строк:   24

SELECT t.name, t.tag,
       COUNT(tm.player_id) players_now,
       COUNT(s.streamer_id) streamers_now
FROM teams AS t
LEFT JOIN team_members AS tm ON tm.team_id = t.team_id AND tm.left_at IS NULL
LEFT JOIN streamers AS s USING (player_id)
GROUP BY t.team_id
ORDER BY players_now DESC, t.name;

