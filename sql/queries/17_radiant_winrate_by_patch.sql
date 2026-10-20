-- 17. Доля побед светлой стороны по патчам.
-- Патч без единого матча не выводится; radiant_winrate — процент,
-- round(100.0 * radiant_wins / matches, 2).
--
-- Колонки: version, matches, radiant_wins, radiant_winrate
-- Порядок: radiant_winrate (округлённое) по убыванию, при равенстве version по возрастанию
-- Строк:   12

SELECT
    p.version, COUNT(*) matches,
    COUNT(*) FILTER (WHERE m.winner = 'radiant') radiant_wins,
    ROUND(100.0 * COUNT(*) FILTER (WHERE m.winner = 'radiant') / COUNT(*), 2) radiant_winrate
FROM patches AS p
JOIN matches AS m USING (patch_id)
GROUP BY p.patch_id
ORDER BY radiant_winrate DESC, p.version;

