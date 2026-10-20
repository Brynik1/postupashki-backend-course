-- 07. Действующие составы: кто сейчас за кого играет.
-- Только незакрытые периоды (left_at IS NULL); игроки без команды не выводятся.
--
-- Колонки: nickname, country, mmr, team_name, joined_at
-- Порядок: joined_at по возрастанию, при равенстве nickname по возрастанию
-- Строк:   86

SELECT
    p.nickname nickname,
    p.country country,
    p.mmr mmr,
    t.name team_name,
    tm.joined_at joined_at
FROM team_members tm
JOIN players p USING (player_id)
JOIN teams t USING (team_id)
WHERE left_at IS NULL
ORDER BY joined_at, nickname;
