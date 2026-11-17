from collections import defaultdict
from collections.abc import Iterable

from app.models import Category


def build_tree(categories: Iterable[Category]) -> list[dict]:
    """扁平分类列表 → 树形嵌套结构（按 sort_order, id 排序）"""
    children_map: dict[int | None, list[Category]] = defaultdict(list)
    for c in categories:
        children_map[c.parent_id].append(c)

    def to_node(c: Category) -> dict:
        return {
            "id": c.id,
            "parent_id": c.parent_id,
            "name": c.name,
            "icon": c.icon,
            "sort_order": c.sort_order,
            "is_enabled": bool(c.is_enabled),
            "remark": c.remark,
            "children": [to_node(child) for child in sorted(
                children_map.get(c.id, []), key=lambda x: (x.sort_order, x.id)
            )],
        }

    roots = sorted(children_map.get(None, []), key=lambda x: (x.sort_order, x.id))
    return [to_node(r) for r in roots]


def collect_descendant_ids(categories: Iterable[Category], root_id: int) -> set[int]:
    """收集某分类及其所有子孙的 id 集合（用于循环引用校验、级联操作）"""
    children_map: dict[int | None, list[int]] = defaultdict(list)
    id_set = set()
    for c in categories:
        children_map[c.parent_id].append(c.id)
        id_set.add(c.id)
    if root_id not in id_set:
        return set()

    result = {root_id}
    queue = [root_id]
    while queue:
        current = queue.pop()
        for child_id in children_map.get(current, []):
            if child_id not in result:
                result.add(child_id)
                queue.append(child_id)
    return result
