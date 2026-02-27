#!/usr/bin/env python3
"""Pygame GUI map renderer with hierarchy support — global view, interior view, breadcrumb navigation."""

import sys
import json
import math
import time
import hashlib
from typing import Dict, Tuple
from pathlib import Path

try:
    import pygame
except ImportError:
    print("[ERROR] Pygame not installed. Install with: uv pip install pygame")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.json_ops import JsonOperations
from connection_utils import get_unique_edges, get_connections

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from force_layout import compute_layout, _cache as _layout_cache

DEFAULT_TERRAIN_COLORS = {
    'default': [100, 150, 255]
}

MAX_TERRAIN_PIXELS = 2000
BREADCRUMB_HEIGHT = 30


def _data_hash(data) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()


class MapGUI:
    """Interactive Pygame map renderer"""

    COLOR_BG = (10, 10, 15)
    COLOR_LOCATION = (100, 200, 255)
    COLOR_PLAYER = (255, 100, 100)
    COLOR_TEXT = (200, 200, 220)
    COLOR_HIGHLIGHT = (255, 255, 100)
    COLOR_BLOCKED = (200, 50, 50, 128)
    COLOR_COMPOUND = (180, 120, 255)
    COLOR_ENTRY = (80, 255, 80)
    COLOR_INTERIOR_LINE = (200, 200, 200)
    COLOR_BREADCRUMB_BG = (30, 30, 50)
    COLOR_BREADCRUMB_SEP = (100, 100, 120)

    def __init__(self, campaign_dir: str, width: int = 1200, height: int = 800):
        self.json_ops = JsonOperations(campaign_dir)
        self.width = width
        self.height = height

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Campaign Map")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('monospace', 14)
        self.font_large = pygame.font.SysFont('monospace', 18, bold=True)

        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.01
        self.max_zoom = 5.0

        self.dragging = False
        self.drag_start = (0, 0)
        self.selected_location = None
        self.hovered_location = None

        self.view_mode = "global"
        self.current_compound = None
        self.breadcrumb = []
        self.interior_layout = {}
        self.interior_edges = []
        self.breadcrumb_rects = []

        self.refresh_btn_rect = pygame.Rect(self.width - 160, self.height - 50, 150, 40)
        self.refresh_btn_hover = False
        self.exit_btn_rect = pygame.Rect(self.width - 320, self.height - 50, 150, 40)
        self.exit_btn_hover = False
        self.enter_btn_rect = pygame.Rect(0, 0, 150, 40)
        self.enter_btn_hover = False

        self.global_terrain_surface = None
        self.global_terrain_bounds = None
        self.global_data_hash = None
        self.terrain_gen_time = 0.0

        self.compound_cache = {}

        self.locations = {}
        self.overview = {}
        self.current_location = None
        self.terrain_colors = {}
        self._load_and_generate_all()

    def _load_terrain_colors(self):
        raw = self.overview.get('terrain_colors') or self.overview.get('campaign_rules', {}).get('terrain_colors', {})
        merged = dict(DEFAULT_TERRAIN_COLORS)
        for key, val in raw.items():
            if isinstance(val, list) and len(val) == 3:
                merged[key] = val
        self.terrain_colors = {k: tuple(v) for k, v in merged.items()}

    def _load_and_generate_all(self):
        print("[STARTUP] Loading data and pre-generating all surfaces...")
        t_start = time.perf_counter()
        self.locations = self.json_ops.load_json("locations.json") or {}
        self.overview = self.json_ops.load_json("campaign-overview.json") or {}
        self.current_location = self.overview.get('player_position', {}).get('current_location')
        self._load_terrain_colors()
        _layout_cache.clear()

        global_data = {n: d for n, d in self.locations.items() if not d.get('parent')}
        new_hash = _data_hash(global_data)
        self.global_data_hash = new_hash
        self.global_terrain_surface = self._generate_global_terrain()
        self._center_camera_global()

        compounds = {n: d for n, d in self.locations.items() if d.get('type') == 'compound'}
        for name in compounds:
            self._generate_compound_cache(name)

        elapsed = time.perf_counter() - t_start
        print(f"[STARTUP] Done in {elapsed:.1f}s — {len(self.locations)} locations, "
              f"{len(compounds)} compounds cached, {len(self.terrain_colors)} terrain types")

    def reload_data(self):
        print("[REFRESH] Checking for changes...")
        t_start = time.perf_counter()
        new_locations = self.json_ops.load_json("locations.json") or {}
        new_overview = self.json_ops.load_json("campaign-overview.json") or {}

        old_terrain_colors = dict(self.terrain_colors)
        self.locations = new_locations
        self.overview = new_overview
        self.current_location = self.overview.get('player_position', {}).get('current_location')
        self._load_terrain_colors()
        terrain_changed = (self.terrain_colors != old_terrain_colors)

        if terrain_changed:
            _layout_cache.clear()

        global_data = {n: d for n, d in self.locations.items() if not d.get('parent')}
        new_global_hash = _data_hash(global_data)
        if new_global_hash != self.global_data_hash or terrain_changed:
            print("[REFRESH] Global map changed — regenerating terrain...")
            self.global_data_hash = new_global_hash
            _layout_cache.clear()
            self.global_terrain_surface = self._generate_global_terrain()
        else:
            print("[REFRESH] Global map unchanged")

        compounds = {n: d for n, d in self.locations.items() if d.get('type') == 'compound'}
        regen_count = 0
        for name in compounds:
            children = self.locations.get(name, {}).get('children', [])
            child_data = {c: self.locations.get(c, {}) for c in children}
            compound_payload = {'compound': self.locations.get(name, {}), 'children': child_data}
            new_hash = _data_hash(compound_payload)

            cached = self.compound_cache.get(name)
            if not cached or cached['data_hash'] != new_hash or terrain_changed:
                print(f"[REFRESH] Compound '{name}' changed — regenerating...")
                self._generate_compound_cache(name)
                regen_count += 1

        for old_name in list(self.compound_cache.keys()):
            if old_name not in compounds:
                del self.compound_cache[old_name]

        if self.view_mode == "interior" and self.current_compound:
            self._apply_compound_cache(self.current_compound)

        elapsed = time.perf_counter() - t_start
        print(f"[REFRESH] Done in {elapsed:.1f}s — {regen_count} compounds regenerated")

    def _generate_compound_cache(self, compound_name: str):
        t_start = time.perf_counter()
        compound_data = self.locations.get(compound_name, {})
        children = compound_data.get('children', [])
        if not children:
            print(f"[COMPOUND] '{compound_name}' — empty, skipping")
            self.compound_cache[compound_name] = {
                'layout': {}, 'edges': [], 'terrain_surface': None,
                'terrain_bounds': None, 'data_hash': ''
            }
            return

        entry_points = compound_data.get('entry_points', [])
        children_set = set(children)
        edges = []
        seen_edges = set()
        for child_name in children:
            for conn in get_connections(child_name, self.locations):
                to_name = conn.get('to') if isinstance(conn, dict) else conn
                if to_name in children_set:
                    edge_key = tuple(sorted([child_name, to_name]))
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append((child_name, to_name))

        print(f"[COMPOUND] '{compound_name}' — {len(children)} rooms, {len(edges)} connections, "
              f"entries: {entry_points}")

        layout_size = 600
        layout = compute_layout(
            children, edges,
            entry_points=entry_points,
            width=layout_size, height=layout_size
        )

        for pos in layout.values():
            pos['x'] = pos['x'] - layout_size / 2
            pos['y'] = layout_size / 2 - pos['y']

        for name, pos in layout.items():
            print(f"[COMPOUND]   {name}: ({pos['x']:.0f}, {pos['y']:.0f})")

        terrain_surface, terrain_bounds = self._generate_interior_terrain(layout, edges)

        elapsed = time.perf_counter() - t_start
        print(f"[COMPOUND] '{compound_name}' done in {elapsed:.1f}s")

        child_data = {c: self.locations.get(c, {}) for c in children}
        compound_payload = {'compound': compound_data, 'children': child_data}

        self.compound_cache[compound_name] = {
            'layout': layout,
            'edges': edges,
            'terrain_surface': terrain_surface,
            'terrain_bounds': terrain_bounds,
            'data_hash': _data_hash(compound_payload)
        }

    def _apply_compound_cache(self, compound_name: str):
        cached = self.compound_cache.get(compound_name)
        if not cached:
            self._generate_compound_cache(compound_name)
            cached = self.compound_cache.get(compound_name, {})

        self.interior_layout = cached.get('layout', {})
        self.interior_edges = cached.get('edges', [])

        if self.interior_layout:
            xs = [p['x'] for p in self.interior_layout.values()]
            ys = [p['y'] for p in self.interior_layout.values()]
            self.camera_x = (min(xs) + max(xs)) / 2
            self.camera_y = (min(ys) + max(ys)) / 2
            self.zoom = 1.0

    def _resolve_player_global_name(self) -> str:
        loc_name = self.current_location or ''
        loc_data = self.locations.get(loc_name, {})
        while loc_data.get('parent'):
            loc_name = loc_data['parent']
            loc_data = self.locations.get(loc_name, {})
        return loc_name

    def _center_camera_global(self):
        if not self.locations:
            return

        player_global = self._resolve_player_global_name()
        player_coords = self.locations.get(player_global, {}).get('coordinates')

        if not player_coords:
            coords_all = [
                loc_data['coordinates']
                for loc_data in self.locations.values()
                if loc_data.get('coordinates') and not loc_data.get('parent')
            ]
            if coords_all:
                self.camera_x = sum(c['x'] for c in coords_all) / len(coords_all)
                self.camera_y = sum(c['y'] for c in coords_all) / len(coords_all)
            return

        fit_points = [(player_coords['x'], player_coords['y'])]

        for conn in get_connections(player_global, self.locations):
            to_name = conn.get('to', '')
            to_data = self.locations.get(to_name, {})
            to_coords = to_data.get('coordinates')
            if to_coords:
                fit_points.append((to_coords['x'], to_coords['y']))

        min_x = min(p[0] for p in fit_points)
        max_x = max(p[0] for p in fit_points)
        min_y = min(p[1] for p in fit_points)
        max_y = max(p[1] for p in fit_points)

        self.camera_x = (min_x + max_x) / 2
        self.camera_y = (min_y + max_y) / 2

        span_x = max_x - min_x
        span_y = max_y - min_y
        if span_x > 0 or span_y > 0:
            padding = 1.5
            zoom_x = self.width / max(1, span_x * padding)
            zoom_y = self.height / max(1, span_y * padding)
            self.zoom = max(self.min_zoom, min(zoom_x, zoom_y, self.max_zoom))
        else:
            self.zoom = 0.15

    def _is_global_visible(self, loc_name: str, loc_data: Dict) -> bool:
        loc_type = loc_data.get('type', 'world')
        parent = loc_data.get('parent')
        if parent:
            return False
        if loc_type in ('world', 'compound'):
            return True
        if loc_type not in ('interior',):
            return True
        return False

    def _is_compound(self, loc_data: Dict) -> bool:
        return loc_data.get('type') == 'compound'

    def enter_compound(self, compound_name: str):
        loc_data = self.locations.get(compound_name, {})
        if not self._is_compound(loc_data):
            return
        self.breadcrumb.append(compound_name)
        self.current_compound = compound_name
        self.view_mode = "interior"
        self.selected_location = None
        self._apply_compound_cache(compound_name)

    def exit_to_level(self, level_index: int):
        if level_index < 0:
            self.view_mode = "global"
            self.current_compound = None
            self.breadcrumb = []
            self.interior_layout = {}
            self._center_camera_global()
            return
        self.breadcrumb = self.breadcrumb[:level_index + 1]
        self.current_compound = self.breadcrumb[-1]
        self.view_mode = "interior"
        self.selected_location = None
        self._apply_compound_cache(self.current_compound)

    def go_up(self):
        if not self.breadcrumb:
            return
        self.breadcrumb.pop()
        if self.breadcrumb:
            self.current_compound = self.breadcrumb[-1]
            self._apply_compound_cache(self.current_compound)
        else:
            self.view_mode = "global"
            self.current_compound = None
            self.interior_layout = {}
            self._center_camera_global()

    def _get_terrain_color(self, loc_name: str) -> Tuple[int, int, int]:
        terrain = self.locations.get(loc_name, {}).get('terrain')
        if terrain and terrain in self.terrain_colors:
            c = self.terrain_colors[terrain]
            return (c[0], c[1], c[2]) if isinstance(c, (list, tuple)) else c
        return self.COLOR_LOCATION

    def _generate_interior_terrain(self, layout, edges):
        if not layout or not edges:
            return None, None

        xs = [p['x'] for p in layout.values()]
        ys = [p['y'] for p in layout.values()]
        margin = 150
        min_x = min(xs) - margin
        max_x = max(xs) + margin
        min_y = min(ys) - margin
        max_y = max(ys) + margin

        world_w = max_x - min_x
        world_h = max_y - min_y
        meters_per_pixel = max(1, math.ceil(max(world_w, world_h) / MAX_TERRAIN_PIXELS))

        surf_w = max(1, int(world_w / meters_per_pixel))
        surf_h = max(1, int(world_h / meters_per_pixel))

        bounds = {
            'min_x': min_x, 'max_x': max_x,
            'min_y': min_y, 'max_y': max_y,
            'meters_per_pixel': meters_per_pixel
        }

        surface = pygame.Surface((surf_w, surf_h))
        surface.fill(self.COLOR_BG)

        segments = []
        for a, b in edges:
            pa = layout.get(a)
            pb = layout.get(b)
            if not pa or not pb:
                continue
            tc_a = self._get_terrain_color(a)
            tc_b = self._get_terrain_color(b)
            bg_a = tuple(int(c * 0.15 + self.COLOR_BG[i] * 0.85) for i, c in enumerate(tc_a))
            bg_b = tuple(int(c * 0.15 + self.COLOR_BG[i] * 0.85) for i, c in enumerate(tc_b))
            segments.append({
                'x1': pa['x'], 'y1': pa['y'],
                'x2': pb['x'], 'y2': pb['y'],
                'color_a': bg_a, 'color_b': bg_b
            })

        node_points = []
        for name, pos in layout.items():
            tc = self._get_terrain_color(name)
            bg = tuple(int(c * 0.15 + self.COLOR_BG[i] * 0.85) for i, c in enumerate(tc))
            node_points.append({'x': pos['x'], 'y': pos['y'], 'color': bg})

        fog_dist = 120
        sample = max(2, int(max(world_w, world_h) / 400))

        print(f"[INTERIOR TERRAIN] {surf_w}x{surf_h}px, sample={sample}, fog={fog_dist}")

        for px in range(0, surf_w, sample):
            for py in range(0, surf_h, sample):
                wx = min_x + px * meters_per_pixel
                wy = max_y - py * meters_per_pixel

                min_dist = float('inf')
                nearest_color = None

                for seg in segments:
                    dist = self.point_to_segment_distance(
                        wx, wy, seg['x1'], seg['y1'], seg['x2'], seg['y2']
                    )
                    if dist < min_dist:
                        min_dist = dist
                        dx_total = seg['x2'] - seg['x1']
                        dy_total = seg['y2'] - seg['y1']
                        seg_len_sq = dx_total * dx_total + dy_total * dy_total
                        if seg_len_sq > 0:
                            t = max(0, min(1, ((wx - seg['x1']) * dx_total + (wy - seg['y1']) * dy_total) / seg_len_sq))
                        else:
                            t = 0.5
                        ca, cb = seg['color_a'], seg['color_b']
                        nearest_color = (
                            int(ca[0] + (cb[0] - ca[0]) * t),
                            int(ca[1] + (cb[1] - ca[1]) * t),
                            int(ca[2] + (cb[2] - ca[2]) * t)
                        )

                for np_ in node_points:
                    dist = math.sqrt((wx - np_['x'])**2 + (wy - np_['y'])**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_color = np_['color']

                if min_dist <= fog_dist and nearest_color:
                    pygame.draw.rect(surface, nearest_color, (px, py, sample, sample))

        return surface, bounds

    def _generate_global_terrain(self):
        t_start = time.perf_counter()
        print("[TERRAIN] Generating global terrain surface...")

        if not self.locations:
            return None

        coords_list = [(loc.get('coordinates', {}).get('x', 0),
                        loc.get('coordinates', {}).get('y', 0))
                       for _, loc in self.locations.items()
                       if loc.get('coordinates') and not loc.get('parent')]

        if not coords_list:
            return None

        margin = 2000
        min_x = min(c[0] for c in coords_list) - margin
        max_x = max(c[0] for c in coords_list) + margin
        min_y = min(c[1] for c in coords_list) - margin
        max_y = max(c[1] for c in coords_list) + margin

        world_w = max_x - min_x
        world_h = max_y - min_y
        max_dim = max(world_w, world_h)
        meters_per_pixel = max(5, math.ceil(max_dim / MAX_TERRAIN_PIXELS))

        surf_width = int(world_w / meters_per_pixel)
        surf_height = int(world_h / meters_per_pixel)

        print(f"[TERRAIN] World: {world_w:.0f}x{world_h:.0f}m, Surface: {surf_width}x{surf_height}px, Scale: 1px={meters_per_pixel}m")

        self.global_terrain_bounds = {
            'min_x': min_x, 'max_x': max_x,
            'min_y': min_y, 'max_y': max_y,
            'meters_per_pixel': meters_per_pixel
        }

        surface = pygame.Surface((surf_width, surf_height))
        surface.fill(self.COLOR_BG)

        default_color = self.terrain_colors.get('default', (100, 150, 255))

        global_locs = {n: d for n, d in self.locations.items() if self._is_global_visible(n, d)}

        connection_lines = []
        for loc_a, loc_b, conn in get_unique_edges(global_locs):
            coords_a = global_locs[loc_a].get('coordinates')
            coords_b = global_locs.get(loc_b, {}).get('coordinates')
            if not coords_a or not coords_b:
                continue
            terrain = conn.get('terrain', 'default')
            color = self.terrain_colors.get(terrain, default_color)
            bg_color = tuple(int(c * 0.15 + self.COLOR_BG[i] * 0.85) for i, c in enumerate(color))
            connection_lines.append({
                'x1': coords_a['x'], 'y1': coords_a['y'],
                'x2': coords_b['x'], 'y2': coords_b['y'],
                'color': bg_color
            })

        FOG_DISTANCE = 1000
        sample = max(4, int(max_dim / 5000))
        total_cols = surf_width // sample

        print(f"[TERRAIN] Rasterizing (sample={sample}px)...")

        for col_idx, px in enumerate(range(0, surf_width, sample)):
            if col_idx % max(1, total_cols // 10) == 0:
                pct = int(col_idx / max(1, total_cols) * 100)
                elapsed = time.perf_counter() - t_start
                print(f"[TERRAIN] {pct}% ({elapsed:.1f}s)")

            for py in range(0, surf_height, sample):
                world_x = min_x + px * meters_per_pixel
                world_y = max_y - py * meters_per_pixel

                min_dist = float('inf')
                nearest_color = None

                for line in connection_lines:
                    dist = self.point_to_segment_distance(
                        world_x, world_y,
                        line['x1'], line['y1'], line['x2'], line['y2']
                    )
                    if dist < min_dist:
                        min_dist = dist
                        nearest_color = line['color']

                if min_dist <= FOG_DISTANCE:
                    pygame.draw.rect(surface, nearest_color, (px, py, sample, sample))

        self.terrain_gen_time = time.perf_counter() - t_start
        print(f"[TERRAIN] Done in {self.terrain_gen_time:.1f}s ({surf_width}x{surf_height}px)")
        return surface

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        screen_x = (world_x - self.camera_x) * self.zoom + self.width // 2
        screen_y = (self.camera_y - world_y) * self.zoom + self.height // 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        world_x = (screen_x - self.width // 2) / self.zoom + self.camera_x
        world_y = self.camera_y - (screen_y - self.height // 2) / self.zoom
        return world_x, world_y

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

    def _blit_terrain_surface(self, surface, bounds):
        if not surface or not bounds:
            return

        mpp = bounds['meters_per_pixel']
        surf_w, surf_h = surface.get_size()
        scale_factor = mpp * self.zoom

        screen_x, screen_y = self.world_to_screen(bounds['min_x'], bounds['max_y'])

        src_x = max(0, int(-screen_x / scale_factor))
        src_y = max(0, int(-screen_y / scale_factor))
        src_x2 = min(surf_w, int((self.width - screen_x) / scale_factor) + 1)
        src_y2 = min(surf_h, int((self.height - screen_y) / scale_factor) + 1)

        src_w = src_x2 - src_x
        src_h = src_y2 - src_y

        if src_w <= 0 or src_h <= 0:
            return

        dst_w = int(src_w * scale_factor)
        dst_h = int(src_h * scale_factor)
        dst_x = screen_x + int(src_x * scale_factor)
        dst_y = screen_y + int(src_y * scale_factor)

        try:
            if dst_w > 0 and dst_h > 0:
                crop = surface.subsurface((src_x, src_y, src_w, src_h))
                scaled = pygame.transform.scale(crop, (dst_w, dst_h))
                self.screen.blit(scaled, (dst_x, dst_y))
        except Exception as e:
            print(f"[TERRAIN] Blit error: {e}")

    def draw_terrain_background(self):
        self._blit_terrain_surface(self.global_terrain_surface, self.global_terrain_bounds)

    def draw_grid(self):
        pass

    def draw_connections(self):
        default_color = self.terrain_colors.get('default', (100, 150, 255))
        global_locs = {n: d for n, d in self.locations.items() if self._is_global_visible(n, d)}
        for loc_a, loc_b, conn in get_unique_edges(global_locs):
            coords_a = global_locs[loc_a].get('coordinates')
            coords_b = global_locs.get(loc_b, {}).get('coordinates')
            if not coords_a or not coords_b:
                continue
            x1, y1 = self.world_to_screen(coords_a['x'], coords_a['y'])
            x2, y2 = self.world_to_screen(coords_b['x'], coords_b['y'])
            terrain = conn.get('terrain', 'default')
            is_highlighted = self.selected_location in (loc_a, loc_b)
            conn_color = self.COLOR_HIGHLIGHT if is_highlighted else self.terrain_colors.get(terrain, default_color)
            line_width = 4 if is_highlighted else 3
            pygame.draw.line(self.screen, conn_color, (x1, y1), (x2, y2), line_width)

            distance = conn.get('distance_meters', 0)
            if distance > 0:
                dist_km = distance / 1000
                mid_x = (x1 + x2) // 2
                mid_y = (y1 + y2) // 2
                label = self.font.render(f"{dist_km:.1f}km", True, conn_color)
                label_rect = label.get_rect(center=(mid_x, mid_y - 20))
                bg_rect = label_rect.inflate(6, 4)
                pygame.draw.rect(self.screen, (20, 20, 30), bg_rect)
                pygame.draw.rect(self.screen, conn_color, bg_rect, 1)
                self.screen.blit(label, label_rect)
                terrain_label = self.font.render(terrain, True, conn_color)
                terrain_rect = terrain_label.get_rect(center=(mid_x, mid_y - 5))
                terrain_bg = terrain_rect.inflate(6, 4)
                pygame.draw.rect(self.screen, (20, 20, 30), terrain_bg)
                pygame.draw.rect(self.screen, conn_color, terrain_bg, 1)
                self.screen.blit(terrain_label, terrain_rect)

    def draw_blocked_ranges(self, loc_name: str, loc_data: Dict):
        coords = loc_data.get('coordinates')
        if not coords:
            return
        blocked_ranges = loc_data.get('blocked_ranges', [])
        if not blocked_ranges:
            return
        x, y = self.world_to_screen(coords['x'], coords['y'])
        radius = 50 * self.zoom
        for block in blocked_ranges:
            from_deg = block['from']
            to_deg = block['to']
            start_angle = math.radians(-(from_deg - 90))
            end_angle = math.radians(-(to_deg - 90))
            surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            rect = surf.get_rect(center=(int(radius), int(radius)))
            pygame.draw.arc(surf, self.COLOR_BLOCKED, rect, end_angle, start_angle, int(radius))
            points = [(int(radius), int(radius))]
            for angle in [start_angle, end_angle]:
                px = int(radius + radius * math.cos(angle))
                py = int(radius + radius * math.sin(angle))
                points.append((px, py))
            if len(points) > 2:
                pygame.draw.polygon(surf, self.COLOR_BLOCKED, points)
            self.screen.blit(surf, (x - int(radius), y - int(radius)))

    def _draw_node(self, x: int, y: int, radius: int, loc_name: str, loc_data: Dict,
                   is_entry: bool = False, is_neighbor: bool = False, label_text: str = "",
                   is_player_loc: bool = False):
        mouse_pos = pygame.mouse.get_pos()
        is_compound = self._is_compound(loc_data)
        is_waypoint = loc_data.get('is_waypoint', False)
        is_current = (loc_name == self.current_location) or is_player_loc
        is_selected = (loc_name == self.selected_location)
        is_hovered = False
        dist = math.sqrt((mouse_pos[0] - x)**2 + (mouse_pos[1] - y)**2)
        if dist < max(radius, 10):
            is_hovered = True
            self.hovered_location = loc_name

        terrain = loc_data.get('terrain')
        terrain_color = tuple(self.terrain_colors.get(terrain, self.COLOR_LOCATION)) if terrain else None

        if is_compound:
            half = max(10, radius)
            color = self.COLOR_PLAYER if is_current else (terrain_color or self.COLOR_COMPOUND)
            if is_neighbor:
                color = (200, 200, 100)
            if is_selected:
                color = self.COLOR_HIGHLIGHT
            if is_hovered or is_selected:
                pygame.draw.rect(self.screen, self.COLOR_HIGHLIGHT,
                                 (x - half - 4, y - half - 4, (half + 4) * 2, (half + 4) * 2), 2)
            elif is_neighbor:
                pygame.draw.rect(self.screen, (200, 200, 100),
                                 (x - half - 4, y - half - 4, (half + 4) * 2, (half + 4) * 2), 1)
            if is_entry:
                pygame.draw.rect(self.screen, self.COLOR_ENTRY,
                                 (x - half - 2, y - half - 2, (half + 2) * 2, (half + 2) * 2), 2)
            surf = pygame.Surface((half * 2, half * 2), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*color, 100), (0, 0, half * 2, half * 2))
            self.screen.blit(surf, (x - half, y - half))
            pygame.draw.rect(self.screen, color, (x - half, y - half, half * 2, half * 2), 2)
        elif is_waypoint:
            color = (255, 150, 0)
            size = max(8, radius)
            triangle_points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
            if is_hovered or is_selected or is_current:
                pygame.draw.polygon(self.screen, self.COLOR_HIGHLIGHT, [
                    (x, y - size - 4), (x - size - 4, y + size + 4), (x + size + 4, y + size + 4)
                ], 2)
            pygame.draw.polygon(self.screen, color, triangle_points)
            pygame.draw.polygon(self.screen, (200, 100, 0), triangle_points, 2)
        else:
            color = self.COLOR_PLAYER if is_current else (terrain_color or self.COLOR_LOCATION)
            if is_neighbor:
                color = (200, 200, 100)
            if is_selected:
                color = self.COLOR_HIGHLIGHT
            if is_hovered or is_selected:
                pygame.draw.circle(self.screen, self.COLOR_HIGHLIGHT, (x, y), radius + 4, 2)
            elif is_neighbor:
                pygame.draw.circle(self.screen, (200, 200, 100), (x, y), radius + 4, 1)
            if is_entry:
                pygame.draw.circle(self.screen, self.COLOR_ENTRY, (x, y), radius + 2, 2)
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 100), (radius, radius), radius)
            self.screen.blit(surf, (x - radius, y - radius))
            pygame.draw.circle(self.screen, color, (x, y), radius, 2)

        text = label_text or loc_name
        label = self.font.render(text, True, self.COLOR_TEXT)
        label_rect = label.get_rect(center=(x, y - radius - 12))
        shadow = self.font.render(text, True, (0, 0, 0))
        self.screen.blit(shadow, (label_rect.x + 1, label_rect.y + 1))
        self.screen.blit(label, label_rect)

    def draw_locations(self):
        self.hovered_location = None
        player_global = self._resolve_player_global_name()

        visible = []
        for loc_name, loc_data in self.locations.items():
            if not self._is_global_visible(loc_name, loc_data):
                continue
            coords = loc_data.get('coordinates')
            if not coords:
                continue
            visible.append((loc_name, loc_data, coords))

        diameters = [d.get('diameter_meters', 100) for _, d, _ in visible]
        min_d = min(diameters) if diameters else 1
        max_d = max(diameters) if diameters else 1
        MIN_PX, MAX_PX = 8, 40

        for loc_name, loc_data, coords in visible:
            x, y = self.world_to_screen(coords['x'], coords['y'])
            diameter_meters = loc_data.get('diameter_meters', 100)
            if max_d > min_d:
                t = (diameter_meters - min_d) / (max_d - min_d)
                node_radius = int(MIN_PX + t * (MAX_PX - MIN_PX))
            else:
                node_radius = int((MIN_PX + MAX_PX) / 2)
            margin = node_radius + 100
            if x < -margin or x > self.width + margin or y < -margin or y > self.height + margin:
                continue
            self.draw_blocked_ranges(loc_name, loc_data)
            is_player_here = (loc_name == player_global)
            self._draw_node(x, y, node_radius, loc_name, loc_data,
                            is_player_loc=is_player_here,
                            label_text=f"{loc_name} ({diameter_meters}m)")

    def _get_selected_neighbors(self) -> set:
        if not self.selected_location:
            return set()
        neighbors = set()
        for a, b in self.interior_edges:
            if a == self.selected_location:
                neighbors.add(b)
            elif b == self.selected_location:
                neighbors.add(a)
        return neighbors

    def draw_interior_terrain_background(self):
        if not self.current_compound:
            return
        cached = self.compound_cache.get(self.current_compound)
        if not cached:
            return
        self._blit_terrain_surface(cached.get('terrain_surface'), cached.get('terrain_bounds'))

    def draw_interior_connections(self):
        if not self.current_compound:
            return
        for a, b in self.interior_edges:
            pos_a = self.interior_layout.get(a)
            pos_b = self.interior_layout.get(b)
            if not pos_a or not pos_b:
                continue
            x1, y1 = self.world_to_screen(pos_a['x'], pos_a['y'])
            x2, y2 = self.world_to_screen(pos_b['x'], pos_b['y'])
            is_highlighted = (self.selected_location in (a, b))
            color = self.COLOR_HIGHLIGHT if is_highlighted else self.COLOR_INTERIOR_LINE
            width = 3 if is_highlighted else 2
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width)

    def draw_interior_locations(self):
        if not self.current_compound:
            return
        compound_data = self.locations.get(self.current_compound, {})
        children = compound_data.get('children', [])
        entry_points = set(compound_data.get('entry_points', []))
        selected_neighbors = self._get_selected_neighbors()
        self.hovered_location = None

        for child_name in children:
            pos = self.interior_layout.get(child_name)
            if not pos:
                continue
            child_data = self.locations.get(child_name, {})
            x, y = self.world_to_screen(pos['x'], pos['y'])
            radius = max(10, int(20 * self.zoom))
            self._draw_node(x, y, radius, child_name, child_data,
                            is_entry=child_name in entry_points,
                            is_neighbor=child_name in selected_neighbors)

    def draw_breadcrumb(self):
        pygame.draw.rect(self.screen, self.COLOR_BREADCRUMB_BG,
                         (0, 0, self.width, BREADCRUMB_HEIGHT))
        pygame.draw.line(self.screen, self.COLOR_BREADCRUMB_SEP,
                         (0, BREADCRUMB_HEIGHT), (self.width, BREADCRUMB_HEIGHT), 1)

        self.breadcrumb_rects = []
        x_offset = 10
        segments = ["World"] + list(self.breadcrumb)

        for i, seg in enumerate(segments):
            is_current = (i == len(segments) - 1)
            color = self.COLOR_HIGHLIGHT if is_current else self.COLOR_TEXT
            text = self.font.render(seg, True, color)
            rect = text.get_rect(midleft=(x_offset, BREADCRUMB_HEIGHT // 2))
            self.screen.blit(text, rect)
            self.breadcrumb_rects.append((rect, i - 1))
            x_offset = rect.right + 5

            if i < len(segments) - 1:
                sep = self.font.render(">", True, self.COLOR_BREADCRUMB_SEP)
                sep_rect = sep.get_rect(midleft=(x_offset, BREADCRUMB_HEIGHT // 2))
                self.screen.blit(sep, sep_rect)
                x_offset = sep_rect.right + 5

    def draw_ui(self):
        campaign_name = self.overview.get('campaign_name', 'Campaign Map')
        ui_y_start = BREADCRUMB_HEIGHT + 5 if self.view_mode == "interior" else 0

        title = self.font_large.render(campaign_name, True, self.COLOR_TEXT)
        self.screen.blit(title, (10, ui_y_start + 10))

        instructions = ["Controls:", "  Scroll - Zoom", "  Drag - Pan", "  Click - Select", "  DblClick - Enter"]
        if self.view_mode == "interior":
            instructions.append("  ESC - Go up")
        else:
            instructions.append("  ESC - Exit")

        y_offset = ui_y_start + 40
        for line in instructions:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

        terrain_to_show = {}
        if self.view_mode == "global":
            for t, c in self.terrain_colors.items():
                if t != 'default':
                    terrain_to_show[t] = c
        elif self.view_mode == "interior" and self.current_compound:
            compound_data = self.locations.get(self.current_compound, {})
            for child_name in compound_data.get('children', []):
                t = self.locations.get(child_name, {}).get('terrain')
                if t and t in self.terrain_colors:
                    terrain_to_show[t] = self.terrain_colors[t]

        if terrain_to_show:
            y_offset += 10
            legend_text = self.font.render("Terrain:", True, self.COLOR_TEXT)
            self.screen.blit(legend_text, (10, y_offset))
            y_offset += 20
            for terrain, color in terrain_to_show.items():
                pygame.draw.circle(self.screen, color, (22, y_offset + 5), 6)
                text = self.font.render(terrain, True, color)
                self.screen.blit(text, (35, y_offset))
                y_offset += 18

        info_lines = [f"Zoom: {self.zoom:.2f}x", f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})"]
        if self.terrain_gen_time > 0 and self.view_mode == "global":
            info_lines.append(f"Terrain: {self.terrain_gen_time:.1f}s")
        if self.view_mode == "interior":
            info_lines.append(f"Interior: {self.current_compound}")

        y_offset = self.height - 80
        for line in info_lines:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

        legend_items = [
            (self.COLOR_PLAYER, "@ Current Position"),
            (self.COLOR_LOCATION, "  Location"),
            (self.COLOR_COMPOUND, "  Compound"),
        ]
        for color, label_txt in legend_items:
            pygame.draw.circle(self.screen, color, (15, y_offset + 5), 5)
            text = self.font.render(label_txt, True, self.COLOR_TEXT)
            self.screen.blit(text, (25, y_offset))
            y_offset += 18

        mouse_pos = pygame.mouse.get_pos()

        if self.view_mode == "interior":
            self.exit_btn_hover = self.exit_btn_rect.collidepoint(mouse_pos)
            eb_color = (180, 80, 80) if self.exit_btn_hover else (130, 50, 50)
            eb_border = (255, 120, 120) if self.exit_btn_hover else (180, 80, 80)
            pygame.draw.rect(self.screen, eb_color, self.exit_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, eb_border, self.exit_btn_rect, 2, border_radius=6)
            eb_text = self.font_large.render("Exit (ESC)", True, (255, 255, 255))
            eb_text_rect = eb_text.get_rect(center=self.exit_btn_rect.center)
            self.screen.blit(eb_text, eb_text_rect)

        show_enter = False
        if self.selected_location:
            sel_data = self.locations.get(self.selected_location, {})
            if self._is_compound(sel_data):
                show_enter = True

        if show_enter:
            if self.view_mode == "interior":
                self.enter_btn_rect = pygame.Rect(self.width - 480, self.height - 50, 150, 40)
            else:
                self.enter_btn_rect = pygame.Rect(self.width - 320, self.height - 50, 150, 40)
            self.enter_btn_hover = self.enter_btn_rect.collidepoint(mouse_pos)
            en_color = (80, 80, 180) if self.enter_btn_hover else (50, 50, 130)
            en_border = (120, 120, 255) if self.enter_btn_hover else (80, 80, 180)
            pygame.draw.rect(self.screen, en_color, self.enter_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, en_border, self.enter_btn_rect, 2, border_radius=6)
            en_text = self.font_large.render("Enter", True, (255, 255, 255))
            en_text_rect = en_text.get_rect(center=self.enter_btn_rect.center)
            self.screen.blit(en_text, en_text_rect)

        self.refresh_btn_hover = self.refresh_btn_rect.collidepoint(mouse_pos)
        btn_color = (80, 180, 80) if self.refresh_btn_hover else (50, 130, 50)
        btn_border = (120, 255, 120) if self.refresh_btn_hover else (80, 180, 80)
        pygame.draw.rect(self.screen, btn_color, self.refresh_btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, btn_border, self.refresh_btn_rect, 2, border_radius=6)
        btn_text = self.font_large.render("Refresh (R)", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=self.refresh_btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)

        if self.selected_location and self.selected_location in self.locations:
            self.draw_location_panel(self.selected_location)

    def draw_location_panel(self, loc_name: str):
        loc_data = self.locations[loc_name]
        coords = loc_data.get('coordinates', {})
        panel_width = 400
        panel_height = 400
        panel_x = self.width - panel_width - 10
        panel_y = 10
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, self.COLOR_TEXT, panel_rect, 2)
        title = self.font_large.render(loc_name, True, self.COLOR_HIGHLIGHT)
        self.screen.blit(title, (panel_x + 10, panel_y + 10))
        y = panel_y + 40
        info_lines = []
        desc = loc_data.get('description', '')
        if desc:
            words = desc.split()
            line = ""
            for w in words:
                if len(line) + len(w) + 1 > 50:
                    info_lines.append(line)
                    line = w
                else:
                    line = f"{line} {w}" if line else w
            if line:
                info_lines.append(line)
            info_lines.append("")
        loc_type = loc_data.get('type', '')
        if loc_type:
            info_lines.append(f"Type: {loc_type}")
        parent = loc_data.get('parent', '')
        if parent:
            info_lines.append(f"Parent: {parent}")
        if coords:
            info_lines.append(f"Coordinates: ({coords.get('x', 0)}, {coords.get('y', 0)})")
        position = loc_data.get('position', '')
        if position:
            info_lines.append(f"Position: {position}")
        children = loc_data.get('children', [])
        if children:
            info_lines.append(f"Children: {', '.join(children)}")
        info_lines.extend(["", "Connections:"])
        for conn in get_connections(loc_name, self.locations):
            to = conn.get('to', '?')
            parts = [to]
            dist = conn.get('distance_meters')
            if dist:
                parts.append(f"{dist}m")
            bearing = conn.get('bearing')
            if bearing is not None:
                parts.append(f"{bearing}°")
            terrain = conn.get('terrain')
            if terrain:
                parts.append(terrain)
            info_lines.append(f"  > {parts[0]} ({', '.join(parts[1:])})" if len(parts) > 1 else f"  > {parts[0]}")
        blocked = loc_data.get('blocked_ranges', [])
        if blocked:
            info_lines.extend(["", "Blocked:"])
            for block in blocked:
                info_lines.append(f"  {block['from']}deg-{block['to']}deg: {block['reason']}")
        for line in info_lines:
            if y > panel_y + panel_height - 20:
                break
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (panel_x + 10, y))
            y += 18

    def _handle_click(self, pos):
        if self.view_mode == "interior":
            for rect, level_idx in self.breadcrumb_rects:
                if rect.collidepoint(pos):
                    self.exit_to_level(level_idx)
                    return

        if self.view_mode == "interior" and self.exit_btn_rect.collidepoint(pos):
            self.go_up()
            return

        if self.refresh_btn_rect.collidepoint(pos):
            self.reload_data()
            return

        if self.enter_btn_rect.collidepoint(pos):
            if self.selected_location and self._is_compound(self.locations.get(self.selected_location, {})):
                self.enter_compound(self.selected_location)
                return

        if self.hovered_location:
            loc_data = self.locations.get(self.hovered_location, {})
            if self.hovered_location == self.selected_location and self._is_compound(loc_data):
                self.enter_compound(self.hovered_location)
                return
            self.selected_location = self.hovered_location
        else:
            self.selected_location = None
            self.dragging = True
            self.drag_start = pos

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.view_mode == "interior":
                        self.go_up()
                    else:
                        return False
                elif event.key == pygame.K_r:
                    self.reload_data()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)
                elif event.button == 4:
                    self.zoom = min(self.zoom * 1.1, self.max_zoom)
                    mx, my = pygame.mouse.get_pos()
                    world_pos = self.screen_to_world(mx, my)
                    new_screen = self.world_to_screen(world_pos[0], world_pos[1])
                    self.camera_x += (new_screen[0] - mx) / self.zoom
                    self.camera_y += (my - new_screen[1]) / self.zoom
                elif event.button == 5:
                    self.zoom = max(self.zoom / 1.1, self.min_zoom)
                    mx, my = pygame.mouse.get_pos()
                    world_pos = self.screen_to_world(mx, my)
                    new_screen = self.world_to_screen(world_pos[0], world_pos[1])
                    self.camera_x += (new_screen[0] - mx) / self.zoom
                    self.camera_y += (my - new_screen[1]) / self.zoom
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = event.pos[0] - self.drag_start[0]
                    dy = event.pos[1] - self.drag_start[1]
                    self.camera_x -= dx / self.zoom
                    self.camera_y += dy / self.zoom
                    self.drag_start = event.pos
        return True

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.screen.fill(self.COLOR_BG)
            if self.view_mode == "global":
                self.draw_terrain_background()
                self.draw_grid()
                self.draw_connections()
                self.draw_locations()
            else:
                self.draw_interior_terrain_background()
                self.draw_interior_connections()
                self.draw_interior_locations()
                self.draw_breadcrumb()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Interactive campaign map')
    parser.add_argument('--width', type=int, default=1200, help='Window width')
    parser.add_argument('--height', type=int, default=800, help='Window height')
    args = parser.parse_args()

    active_campaign_file = Path("world-state/active-campaign.txt")
    if not active_campaign_file.exists():
        print("[ERROR] No active campaign")
        sys.exit(1)

    active_campaign = active_campaign_file.read_text().strip()
    campaign_dir = Path(f"world-state/campaigns/{active_campaign}")
    gui = MapGUI(str(campaign_dir), width=args.width, height=args.height)
    gui.run()


if __name__ == "__main__":
    main()
