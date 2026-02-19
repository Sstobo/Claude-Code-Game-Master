#!/usr/bin/env python3
"""
Pygame GUI map renderer for campaign visualization
Interactive visual map with zoom, pan, and location info
"""

import sys
import math
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path

try:
    import pygame
except ImportError:
    print("[ERROR] Pygame not installed. Install with: uv pip install pygame")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.json_ops import JsonOperations
from connection_utils import get_unique_edges

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from path_intersect import check_path_intersection

DEFAULT_TERRAIN_COLORS = {
    'open': [100, 200, 100],
    'forest': [50, 150, 50],
    'urban': [150, 150, 150],
    'water': [50, 150, 255],
    'mountain': [120, 120, 120],
    'desert': [255, 200, 100],
    'swamp': [100, 120, 80],
    'default': [100, 150, 255]
}

MAX_TERRAIN_PIXELS = 2000


class MapGUI:
    """Interactive Pygame map renderer"""

    COLOR_BG = (10, 10, 15)
    COLOR_LOCATION = (100, 200, 255)
    COLOR_PLAYER = (255, 100, 100)
    COLOR_TEXT = (200, 200, 220)
    COLOR_HIGHLIGHT = (255, 255, 100)
    COLOR_BLOCKED = (200, 50, 50, 128)

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

        self.refresh_btn_rect = pygame.Rect(self.width - 160, self.height - 50, 150, 40)
        self.refresh_btn_hover = False

        self.terrain_surface = None
        self.terrain_bounds = None
        self.terrain_gen_time = 0.0

        self.locations = {}
        self.overview = {}
        self.current_location = None
        self.terrain_colors = {}
        self.reload_data()

    def _load_terrain_colors(self):
        raw = self.overview.get('terrain_colors', {})
        merged = dict(DEFAULT_TERRAIN_COLORS)
        for key, val in raw.items():
            if isinstance(val, list) and len(val) == 3:
                merged[key] = val
        self.terrain_colors = {k: tuple(v) for k, v in merged.items()}

    def reload_data(self):
        print("[RELOAD] Reloading data from JSON files...")
        self.locations = self.json_ops.load_json("locations.json") or {}
        self.overview = self.json_ops.load_json("campaign-overview.json") or {}
        self.current_location = self.overview.get('player_position', {}).get('current_location')
        self._load_terrain_colors()
        print(f"[RELOAD] Loaded {len(self.locations)} locations, {len(self.terrain_colors)} terrain types")
        print(f"[RELOAD] Current location: {self.current_location}")
        print("[RELOAD] Data reloaded!")

        self.terrain_surface = None

        if self.locations:
            coords_list = [
                (loc_data.get('coordinates', {}).get('x', 0),
                 loc_data.get('coordinates', {}).get('y', 0))
                for loc_data in self.locations.values()
                if loc_data.get('coordinates')
            ]
            if coords_list:
                avg_x = sum(c[0] for c in coords_list) / len(coords_list)
                avg_y = sum(c[1] for c in coords_list) / len(coords_list)
                self.camera_x = avg_x
                self.camera_y = avg_y

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

    def generate_static_terrain_surface(self):
        t_start = time.perf_counter()
        print("[TERRAIN] Generating static terrain surface...")

        if not self.locations:
            return None

        coords_list = [(loc.get('coordinates', {}).get('x', 0),
                        loc.get('coordinates', {}).get('y', 0))
                       for loc in self.locations.values()
                       if loc.get('coordinates')]

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

        self.terrain_bounds = {
            'min_x': min_x, 'max_x': max_x,
            'min_y': min_y, 'max_y': max_y,
            'meters_per_pixel': meters_per_pixel
        }

        surface = pygame.Surface((surf_width, surf_height))
        surface.fill(self.COLOR_BG)

        default_color = self.terrain_colors.get('default', (100, 150, 255))

        connection_lines = []
        for loc_a, loc_b, conn in get_unique_edges(self.locations):
            coords_a = self.locations[loc_a].get('coordinates')
            coords_b = self.locations.get(loc_b, {}).get('coordinates')
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

    def draw_terrain_background(self):
        if self.terrain_surface is None:
            self.terrain_surface = self.generate_static_terrain_surface()

        if self.terrain_surface is None or self.terrain_bounds is None:
            self.screen.fill(self.COLOR_BG)
            return

        bounds = self.terrain_bounds
        mpp = bounds['meters_per_pixel']
        surf_w, surf_h = self.terrain_surface.get_size()
        pixels_per_meter = self.zoom
        scale_factor = mpp * pixels_per_meter

        screen_x, screen_y = self.world_to_screen(bounds['min_x'], bounds['max_y'])

        # Crop source rect to visible screen area only
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
                crop = self.terrain_surface.subsurface((src_x, src_y, src_w, src_h))
                scaled = pygame.transform.scale(crop, (dst_w, dst_h))
                self.screen.blit(scaled, (dst_x, dst_y))
        except Exception as e:
            print(f"[TERRAIN] Blit error: {e}")

    def draw_grid(self):
        pass

    def draw_connections(self):
        default_color = self.terrain_colors.get('default', (100, 150, 255))
        for loc_a, loc_b, conn in get_unique_edges(self.locations):
            coords_a = self.locations[loc_a].get('coordinates')
            coords_b = self.locations.get(loc_b, {}).get('coordinates')
            if not coords_a or not coords_b:
                continue
            x1, y1 = self.world_to_screen(coords_a['x'], coords_a['y'])
            x2, y2 = self.world_to_screen(coords_b['x'], coords_b['y'])
            to_loc = loc_b
            terrain = conn.get('terrain', 'default')
            conn_color = self.terrain_colors.get(terrain, default_color)
            pygame.draw.line(self.screen, conn_color, (x1, y1), (x2, y2), 3)

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

    def draw_locations(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_location = None
        for loc_name, loc_data in self.locations.items():
            coords = loc_data.get('coordinates')
            if not coords:
                continue
            x, y = self.world_to_screen(coords['x'], coords['y'])
            diameter_meters = loc_data.get('diameter_meters', 10)
            radius_screen = (diameter_meters / 2) * self.zoom
            margin = radius_screen + 100
            if x < -margin or x > self.width + margin or y < -margin or y > self.height + margin:
                continue
            self.draw_blocked_ranges(loc_name, loc_data)
            is_waypoint = loc_data.get('is_waypoint', False)
            is_current = (loc_name == self.current_location)
            is_selected = (loc_name == self.selected_location)
            is_hovered = False
            dist = math.sqrt((mouse_pos[0] - x)**2 + (mouse_pos[1] - y)**2)
            if dist < max(radius_screen, 10):
                is_hovered = True
                self.hovered_location = loc_name
            if is_waypoint:
                color = (255, 150, 0)
                size = max(8, int(radius_screen))
                triangle_points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
                if is_hovered or is_selected or is_current:
                    pygame.draw.polygon(self.screen, self.COLOR_HIGHLIGHT, [
                        (x, y - size - 4), (x - size - 4, y + size + 4), (x + size + 4, y + size + 4)
                    ], 2)
                pygame.draw.polygon(self.screen, color, triangle_points)
                pygame.draw.polygon(self.screen, (200, 100, 0), triangle_points, 2)
            else:
                color = self.COLOR_PLAYER if is_current else self.COLOR_LOCATION
                if is_selected:
                    color = self.COLOR_HIGHLIGHT
                if is_hovered or is_selected:
                    pygame.draw.circle(self.screen, self.COLOR_HIGHLIGHT, (x, y), int(radius_screen + 6), 2)
                surf = pygame.Surface((int(radius_screen * 2), int(radius_screen * 2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, 100), (int(radius_screen), int(radius_screen)), int(radius_screen))
                self.screen.blit(surf, (x - int(radius_screen), y - int(radius_screen)))
                pygame.draw.circle(self.screen, color, (x, y), int(radius_screen), 2)
            label_text = f"{loc_name} ({diameter_meters}m)"
            label = self.font.render(label_text, True, self.COLOR_TEXT)
            label_rect = label.get_rect(center=(x, y - radius_screen - 15))
            shadow = self.font.render(label_text, True, (0, 0, 0))
            self.screen.blit(shadow, (label_rect.x + 1, label_rect.y + 1))
            self.screen.blit(label, label_rect)

    def draw_ui(self):
        campaign_name = self.overview.get('campaign_name', 'Campaign Map')
        title = self.font_large.render(campaign_name, True, self.COLOR_TEXT)
        self.screen.blit(title, (10, 10))

        instructions = [
            "Controls:",
            "  Scroll - Zoom",
            "  Drag - Pan",
            "  Click - Select",
            "  ESC - Exit",
        ]
        y_offset = 40
        for line in instructions:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

        y_offset += 10
        legend_text = self.font.render("Terrain:", True, self.COLOR_TEXT)
        self.screen.blit(legend_text, (10, y_offset))
        y_offset += 20
        for terrain, color in self.terrain_colors.items():
            if terrain == 'default':
                continue
            pygame.draw.line(self.screen, color, (15, y_offset + 5), (35, y_offset + 5), 3)
            text = self.font.render(terrain, True, color)
            self.screen.blit(text, (40, y_offset))
            y_offset += 18

        info_lines = [
            f"Zoom: {self.zoom:.2f}x",
            f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})",
        ]
        if self.terrain_gen_time > 0:
            info_lines.append(f"Terrain: {self.terrain_gen_time:.1f}s")

        y_offset = self.height - 80
        for line in info_lines:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

        legend_items = [
            (self.COLOR_PLAYER, "@ Current Position"),
            (self.COLOR_LOCATION, "  Location")
        ]
        for color, label in legend_items:
            pygame.draw.circle(self.screen, color, (15, y_offset + 5), 5)
            text = self.font.render(label, True, self.COLOR_TEXT)
            self.screen.blit(text, (25, y_offset))
            y_offset += 18

        mouse_pos = pygame.mouse.get_pos()
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
        panel_height = 300
        panel_x = self.width - panel_width - 10
        panel_y = 10
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, self.COLOR_TEXT, panel_rect, 2)
        title = self.font_large.render(loc_name, True, self.COLOR_HIGHLIGHT)
        self.screen.blit(title, (panel_x + 10, panel_y + 10))
        y = panel_y + 40
        info_lines = [
            f"Position: {loc_data.get('position', 'unknown')}",
            f"Coordinates: ({coords.get('x', 0)}, {coords.get('y', 0)})",
            "", "Connections:"
        ]
        for conn in loc_data.get('connections', []):
            info_lines.append(f"  > {conn.get('to', '?')} ({conn.get('distance_meters', 0)}m, {conn.get('bearing', 0)}deg)")
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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    self.reload_data()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.refresh_btn_rect.collidepoint(event.pos):
                        self.reload_data()
                    elif self.hovered_location:
                        self.selected_location = self.hovered_location
                    else:
                        self.dragging = True
                        self.drag_start = event.pos
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
            self.draw_terrain_background()
            self.draw_grid()
            self.draw_connections()
            self.draw_locations()
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
