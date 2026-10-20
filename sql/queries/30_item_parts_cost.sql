-- 30. Стоимость сборки из базовых составляющих против собственной цены предмета.
-- Берутся предметы со строками в item_recipe, сборка раскрывается до базовых (тех, у кого
-- строк в item_recipe нет, свитки тоже), количества по пути перемножаются; diff = parts_cost - cost.
--
-- Колонки: name, cost, parts_cost, base_parts, diff
-- Порядок: diff по убыванию, при равенстве name по возрастанию
-- Строк:   77

WITH RECURSIVE parts AS (
    SELECT
        item_id root_id,
        component_id,
        quantity qty_total
    FROM item_recipe

    UNION ALL

    SELECT
        p.root_id,
        r.component_id,
        p.qty_total * r.quantity
    FROM parts p
    JOIN item_recipe r ON r.item_id = p.component_id
), totals AS (
    SELECT
        p.root_id,
        SUM(c.cost * p.qty_total) parts_cost,
        SUM(p.qty_total) base_parts
    FROM parts p
    JOIN items c ON c.item_id = p.component_id
    WHERE NOT EXISTS (SELECT 1 FROM item_recipe r WHERE r.item_id = p.component_id)
    GROUP BY p.root_id
)
SELECT
    i.name,
    i.cost,
    t.parts_cost,
    t.base_parts,
    t.parts_cost - i.cost diff
FROM totals t
JOIN items i ON i.item_id = t.root_id
ORDER BY diff DESC, i.name;

