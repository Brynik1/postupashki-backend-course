-- 29. Полное дерево сборки Guardian Greaves, Bloodthorn, Harpoon и Hurricane Pike.
-- Строка на каждый путь вниз, сам корень не выводится; lvl с 1, qty — quantity последнего
-- шага, qty_total — произведение quantity по пути, path — имена от корня через ' > '.
--
-- Колонки: root_item, lvl, component, qty, qty_total, path
-- Порядок: root_item по возрастанию, затем path по возрастанию
-- Строк:   34

WITH RECURSIVE component_tree AS (
    SELECT
        i.name root_item,
        1 lvl,
        c.item_id component_id,
        c.name component,
        r.quantity qty,
        r.quantity qty_total,
        i.name || ' > ' || c.name path
    FROM items i
    JOIN item_recipe r ON r.item_id = i.item_id
    JOIN items c ON c.item_id = r.component_id
    WHERE i.name IN ('Guardian Greaves', 'Bloodthorn', 'Harpoon', 'Hurricane Pike')

    UNION ALL

    SELECT
        tree.root_item,
        tree.lvl + 1,
        c.item_id,
        c.name,
        r.quantity,
        tree.qty_total * r.quantity,
        tree.path || ' > ' || c.name
    FROM component_tree AS tree
    JOIN item_recipe AS r ON r.item_id = tree.component_id
    JOIN items AS c ON c.item_id = r.component_id
)
SELECT root_item, lvl, component, qty, qty_total, path
FROM component_tree
ORDER BY root_item, path;

