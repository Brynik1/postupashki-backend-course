-- 03. Страны, из которых есть игроки с рейтингом не ниже 10000.
-- mmr >= 10000; каждая страна в ответе ровно один раз.
--
-- Колонки: country
-- Порядок: country по возрастанию
-- Строк:   15

SELECT country
FROM players
WHERE mmr >= 10000
GROUP BY country
ORDER BY country;
