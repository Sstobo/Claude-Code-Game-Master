"""Radial tree layout for interior node graphs. Hub nodes in center, leaves radiate outward. Zero crossings for tree-like graphs."""

import math
from collections import deque

_cache: dict = {}

_SNAP_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]


def _cache_key(nodes, edges):
    return (frozenset(nodes), frozenset(edges))


def _neighbors(node, edges):
    result = set()
    for s, d in edges:
        if s == node:
            result.add(d)
        elif d == node:
            result.add(s)
    return result


def _find_hub(nodes, edges):
    best = None
    best_deg = -1
    for n in nodes:
        deg = len(_neighbors(n, edges))
        if deg > best_deg:
            best_deg = deg
            best = n
    return best


def _snap_angle(angle_deg):
    angle_deg = angle_deg % 360
    best = min(_SNAP_ANGLES, key=lambda a: min(abs(angle_deg - a), 360 - abs(angle_deg - a)))
    return best


def _bfs_tree(root, nodes, edges):
    node_set = set(nodes)
    parent_map = {root: None}
    children_map = {n: [] for n in nodes}
    order = [root]
    queue = deque([root])
    seen = {root}

    while queue:
        current = queue.popleft()
        for nb in sorted(_neighbors(current, edges)):
            if nb not in seen and nb in node_set:
                seen.add(nb)
                parent_map[nb] = current
                children_map[current].append(nb)
                order.append(nb)
                queue.append(nb)

    for n in nodes:
        if n not in seen:
            order.append(n)
            parent_map[n] = None

    return parent_map, children_map, order


def _subtree_size(node, children_map):
    count = 1
    for child in children_map.get(node, []):
        count += _subtree_size(child, children_map)
    return count


def compute_layout(nodes, edges, entry_points=None, width=800, height=600, iterations=100):
    if not nodes:
        return {}

    key = _cache_key(nodes, edges)
    if key in _cache:
        return _cache[key]

    node_list = list(nodes)
    n = len(node_list)
    entry_set = set(entry_points or [])

    if n == 1:
        result = {node_list[0]: {"x": width / 2.0, "y": height / 2.0}}
        _cache[key] = result
        return result

    hub = _find_hub(node_list, edges)
    _, children_map, _ = _bfs_tree(hub, node_list, edges)

    cx, cy = width / 2.0, height / 2.0
    positions = {}
    positions[hub] = {"x": cx, "y": cy}

    hub_children = children_map.get(hub, [])
    if hub_children:
        sizes = [_subtree_size(c, children_map) for c in hub_children]
        total = sum(sizes)

        base_angle = 0
        for ep in entry_set:
            if ep in hub_children:
                idx = hub_children.index(ep)
                base_angle = 270 - int(360 * sum(sizes[:idx]) / total + 360 * sizes[idx] / (2 * total))
                break

        ring_radius = min(width, height) * 0.3

        current_angle = base_angle
        for i, child in enumerate(hub_children):
            wedge = 360.0 * sizes[i] / total
            angle_deg = current_angle + wedge / 2.0
            angle_deg = _snap_angle(angle_deg)
            angle_rad = math.radians(angle_deg)

            child_x = cx + ring_radius * math.cos(angle_rad)
            child_y = cy - ring_radius * math.sin(angle_rad)
            positions[child] = {"x": child_x, "y": child_y}

            _layout_subtree(child, angle_deg, ring_radius, children_map, positions, cx, cy, width, height)

            current_angle += wedge

    for nd in node_list:
        if nd not in positions:
            positions[nd] = {"x": cx, "y": cy}

    margin = 40
    all_x = [p["x"] for p in positions.values()]
    all_y = [p["y"] for p in positions.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    range_x = max_x - min_x if max_x > min_x else 1
    range_y = max_y - min_y if max_y > min_y else 1

    for nd in positions:
        positions[nd]["x"] = margin + (positions[nd]["x"] - min_x) / range_x * (width - 2 * margin)
        positions[nd]["y"] = margin + (positions[nd]["y"] - min_y) / range_y * (height - 2 * margin)

    _cache[key] = positions
    return positions


def _layout_subtree(node, parent_angle, parent_radius, children_map, positions, cx, cy, width, height):
    kids = children_map.get(node, [])
    if not kids:
        return

    step_radius = min(width, height) * 0.2
    node_radius = parent_radius + step_radius

    if len(kids) == 1:
        angle_deg = _snap_angle(parent_angle)
        angle_rad = math.radians(angle_deg)
        child_x = cx + node_radius * math.cos(angle_rad)
        child_y = cy - node_radius * math.sin(angle_rad)
        positions[kids[0]] = {"x": child_x, "y": child_y}
        _layout_subtree(kids[0], angle_deg, node_radius, children_map, positions, cx, cy, width, height)
        return

    sizes = [_subtree_size(k, children_map) for k in kids]
    total = sum(sizes)
    spread = min(90, 30 * len(kids))
    start_angle = parent_angle - spread / 2

    current_angle = start_angle
    for i, kid in enumerate(kids):
        wedge = spread * sizes[i] / total
        angle_deg = current_angle + wedge / 2.0
        angle_deg = _snap_angle(angle_deg)
        angle_rad = math.radians(angle_deg)
        child_x = cx + node_radius * math.cos(angle_rad)
        child_y = cy - node_radius * math.sin(angle_rad)
        positions[kid] = {"x": child_x, "y": child_y}
        _layout_subtree(kid, angle_deg, node_radius, children_map, positions, cx, cy, width, height)
        current_angle += wedge
