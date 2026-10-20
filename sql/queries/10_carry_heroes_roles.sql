-- 10. Все роли героев, которые умеют быть керри.
-- Только герои с ролью 'carry'; у каждого выводятся все его роли, по строке на роль.
--
-- Колонки: name, primary_attr, attack_type, role
-- Порядок: name по возрастанию, внутри героя role по возрастанию
-- Строк:   47

SELECT
    h.name,
    h.primary_attr,
    h.attack_type,
    r.role
FROM heroes h
JOIN hero_roles hr USING (hero_id)
JOIN hero_roles r USING (hero_id)
WHERE hr.role = 'carry'
ORDER BY h.name, r.role;

