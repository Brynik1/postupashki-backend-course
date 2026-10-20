-- 28. Три самых дорогих предмета в каждой категории лавки.
-- Категория: 'recipe' при is_recipe, иначе 'assembled' при строках в item_recipe.item_id,
-- иначе 'basic'; place 1-3 по cost убыв., при равной цене по name; purchases — строк match_items, иначе 0.
--
-- Колонки: category, place, name, cost, purchases
-- Порядок: category по возрастанию, затем place по возрастанию
-- Строк:   9

WITH categorized AS (
    SELECT
        i.*,
        CASE
            WHEN is_recipe THEN 'recipe'
            WHEN EXISTS (
                SELECT 1
                FROM item_recipe r
                WHERE r.item_id = i.item_id
            ) THEN 'assembled'
            ELSE 'basic'
        END category
    FROM items i
), ranked AS (
    SELECT
        c.*,
        (
            SELECT COUNT(*) + 1
            FROM categorized AS other
            WHERE other.category = c.category
              AND (
                  other.cost > c.cost
                  OR (
                      other.cost = c.cost
                      AND other.name < c.name
                  )
              )
        ) place
    FROM categorized c
)
SELECT
    r.category,
    r.place,
    r.name,
    r.cost,
    (
        SELECT COUNT(*)
        FROM match_items AS mi
        WHERE mi.item_id = r.item_id
    ) purchases
FROM ranked r
WHERE r.place <= 3
ORDER BY r.category, r.place;

