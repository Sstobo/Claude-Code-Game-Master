#!/usr/bin/env python3
"""
Pygame GUI map renderer for campaign visualization
Interactive visual map with zoom, pan, and location info
"""

import sys
import math
from typing import Dict, List, Tuple, Optional
from pathlib import Path

try:
    import pygame
except ImportError:
    print("[ERROR] Pygame not installed. Install with: uv pip install pygame")
    sys.exit(1)

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from path_intersect import check_path_intersection


class MapGUI:
    """Interactive Pygame map renderer"""

    # Colors
    COLOR_BG = (10, 10, 15)  # Туман войны - неисследованная территория
    COLOR_GRID = (40, 40, 50)
    COLOR_LOCATION = (100, 200, 255)  # Обычная локация (синяя)
    COLOR_PLAYER = (255, 100, 100)  # Текущая позиция игрока (красная)
    COLOR_TEXT = (200, 200, 220)
    COLOR_HIGHLIGHT = (255, 255, 100)
    COLOR_BLOCKED = (200, 50, 50, 128)

    # Terrain colors for connections (только поверхность!)
    TERRAIN_COLORS = {
        'open': (100, 200, 100),      # Зелёный - открытая местность
        'forest': (50, 150, 50),      # Тёмно-зелёный - лес
        'urban': (150, 150, 150),     # Серый - город
        'water': (50, 150, 255),      # Голубой - вода
        'mountain': (120, 120, 120),  # Тёмно-серый - горы
        'desert': (255, 200, 100),    # Жёлтый - пустыня
        'swamp': (100, 120, 80),      # Болотный - болото
        'default': (100, 150, 255)    # Синий - по умолчанию
    }

    def __init__(self, campaign_dir: str, width: int = 1200, height: int = 800):
        self.json_ops = JsonOperations(campaign_dir)
        self.width = width
        self.height = height

        # Pygame initialization
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Campaign Map")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('monospace', 14)
        self.font_large = pygame.font.SysFont('monospace', 18, bold=True)

        # Camera state
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Interaction state
        self.dragging = False
        self.drag_start = (0, 0)
        self.selected_location = None
        self.hovered_location = None

        # Terrain background - STATIC surface, generated once
        self.terrain_surface = None
        self.terrain_bounds = None

        # Load data
        self.locations = {}
        self.overview = {}
        self.current_location = None
        self.reload_data()

    def reload_data(self):
        """Reload campaign data"""
        print("[RELOAD] Reloading data from JSON files...")
        self.locations = self.json_ops.load_json("locations.json") or {}
        self.overview = self.json_ops.load_json("campaign-overview.json") or {}
        self.current_location = self.overview.get('player_position', {}).get('current_location')
        print(f"[RELOAD] Loaded {len(self.locations)} locations")
        print(f"[RELOAD] Current location: {self.current_location}")
        print("[RELOAD] ✓ Data reloaded!")

        # Regenerate terrain surface
        self.terrain_surface = None

        # Calculate bounds for initial camera position
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
        """Convert world coordinates to screen coordinates"""
        # Center on camera, apply zoom, flip Y (screen Y increases downward)
        screen_x = (world_x - self.camera_x) * self.zoom + self.width // 2
        screen_y = (self.camera_y - world_y) * self.zoom + self.height // 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - self.width // 2) / self.zoom + self.camera_x
        world_y = self.camera_y - (screen_y - self.height // 2) / self.zoom
        return world_x, world_y

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Calculate shortest distance from point to line segment"""
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)

        t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

    def generate_static_terrain_surface(self):
        """
        Generate HUGE static terrain surface ONCE
        Then just blit it every frame (super fast!)
        """
        print("[TERRAIN] Generating static terrain surface...")

        if not self.locations:
            return None

        # Calculate world bounds
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

        # Resolution: 1 pixel = 5 meters
        meters_per_pixel = 5
        surf_width = int((max_x - min_x) / meters_per_pixel)
        surf_height = int((max_y - min_y) / meters_per_pixel)

        print(f"[TERRAIN] Surface size: {surf_width}x{surf_height} px")

        # Store bounds for coordinate transformation
        self.terrain_bounds = {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'meters_per_pixel': meters_per_pixel
        }

        # Create surface
        surface = pygame.Surface((surf_width, surf_height))
        surface.fill((10, 10, 15))  # Fog of war

        # Collect connection lines
        connection_lines = []
        for loc_name, loc_data in self.locations.items():
            coords = loc_data.get('coordinates')
            if not coords:
                continue

            for conn in loc_data.get('connections', []):
                to_loc = conn.get('to')
                if to_loc not in self.locations:
                    continue

                to_coords = self.locations[to_loc].get('coordinates')
                if not to_coords:
                    continue

                terrain = conn.get('terrain', 'default')
                color = self.TERRAIN_COLORS.get(terrain, self.TERRAIN_COLORS['default'])
                bg_color = tuple(int(c * 0.15 + self.COLOR_BG[i] * 0.85)
                               for i, c in enumerate(color))

                connection_lines.append({
                    'x1': coords['x'],
                    'y1': coords['y'],
                    'x2': to_coords['x'],
                    'y2': to_coords['y'],
                    'color': bg_color
                })

        # Rasterize terrain
        FOG_DISTANCE = 1000
        sample = 8  # Sample every N pixels for speed

        print("[TERRAIN] Rasterizing (this takes ~30 sec, only once)...")

        for px in range(0, surf_width, sample):
            if px % 100 == 0:
                print(f"[TERRAIN] Progress: {int(px/surf_width*100)}%")

            for py in range(0, surf_height, sample):
                # Convert pixel to world coords
                world_x = min_x + px * meters_per_pixel
                world_y = max_y - py * meters_per_pixel  # Flip Y

                # Find nearest path
                min_dist = float('inf')
                nearest_color = None

                for line in connection_lines:
                    dist = self.point_to_segment_distance(
                        world_x, world_y,
                        line['x1'], line['y1'],
                        line['x2'], line['y2']
                    )

                    if dist < min_dist:
                        min_dist = dist
                        nearest_color = line['color']

                # Draw if within fog distance
                if min_dist <= FOG_DISTANCE:
                    pygame.draw.rect(surface, nearest_color,
                                   (px, py, sample, sample))

        print("[TERRAIN] ✓ Static terrain surface generated!")
        return surface

    def draw_terrain_background(self):
        """
        Draw terrain - transform entire surface like other game objects
        Simple approach: treat terrain surface as one big sprite
        """
        if self.terrain_surface is None:
            self.terrain_surface = self.generate_static_terrain_surface()

        if self.terrain_surface is None or self.terrain_bounds is None:
            self.screen.fill(self.COLOR_BG)
            return

        bounds = self.terrain_bounds
        mpp = bounds['meters_per_pixel']

        # Surface represents world from (min_x, min_y) to (max_x, max_y)
        # Its top-left corner is at world coordinate (min_x, max_y)
        world_origin_x = bounds['min_x']
        world_origin_y = bounds['max_y']

        # Transform surface origin to screen coordinates
        # This is where the surface's top-left corner appears on screen
        screen_x, screen_y = self.world_to_screen(world_origin_x, world_origin_y)

        # Calculate how big the surface appears on screen with current zoom
        surf_width, surf_height = self.terrain_surface.get_size()
        screen_w = int(surf_width * mpp * self.zoom)
        screen_h = int(surf_height * mpp * self.zoom)

        try:
            # Scale entire surface to screen size with zoom
            if screen_w > 0 and screen_h > 0:
                # Use scale() instead of smoothscale() to avoid darkening
                scaled = pygame.transform.scale(
                    self.terrain_surface,
                    (screen_w, screen_h)
                )
                # Blit at transformed position
                self.screen.blit(scaled, (screen_x, screen_y))
            else:
                self.screen.fill(self.COLOR_BG)

        except Exception as e:
            print(f"[TERRAIN] Blit error: {e}")
            print(f"  screen_pos=({screen_x}, {screen_y}), screen_size=({screen_w}, {screen_h})")
            print(f"  camera=({self.camera_x:.1f}, {self.camera_y:.1f}), zoom={self.zoom:.3f}")
            self.screen.fill(self.COLOR_BG)

    def draw_grid(self):
        """Draw coordinate grid (disabled)"""
        # Grid removed per user request
        pass

    def draw_connections(self):
        """Draw connections between locations"""
        for loc_name, loc_data in self.locations.items():
            coords = loc_data.get('coordinates')
            if not coords:
                continue

            x1, y1 = self.world_to_screen(coords['x'], coords['y'])

            for conn in loc_data.get('connections', []):
                to_loc = conn.get('to')
                if to_loc not in self.locations:
                    continue

                to_coords = self.locations[to_loc].get('coordinates')
                if not to_coords:
                    continue

                x2, y2 = self.world_to_screen(to_coords['x'], to_coords['y'])

                # Get terrain type and color
                terrain = conn.get('terrain', 'default')
                conn_color = self.TERRAIN_COLORS.get(terrain, self.TERRAIN_COLORS['default'])

                # Просто линия, БЕЗ стрелок
                pygame.draw.line(self.screen, conn_color, (x1, y1), (x2, y2), 3)

                # Draw distance and terrain labels at midpoint
                distance = conn.get('distance_meters', 0)
                if distance > 0:
                    dist_km = distance / 1000
                    dist_text = f"{dist_km:.1f}km"

                    # Calculate midpoint
                    mid_x = (x1 + x2) // 2
                    mid_y = (y1 + y2) // 2

                    # Distance label
                    label = self.font.render(dist_text, True, conn_color)
                    label_rect = label.get_rect(center=(mid_x, mid_y - 20))
                    bg_rect = label_rect.inflate(6, 4)
                    pygame.draw.rect(self.screen, (20, 20, 30), bg_rect)
                    pygame.draw.rect(self.screen, conn_color, bg_rect, 1)
                    self.screen.blit(label, label_rect)

                    # Terrain label
                    terrain_label = self.font.render(terrain, True, conn_color)
                    terrain_rect = terrain_label.get_rect(center=(mid_x, mid_y - 5))
                    terrain_bg = terrain_rect.inflate(6, 4)
                    pygame.draw.rect(self.screen, (20, 20, 30), terrain_bg)
                    pygame.draw.rect(self.screen, conn_color, terrain_bg, 1)
                    self.screen.blit(terrain_label, terrain_rect)

    def draw_blocked_ranges(self, loc_name: str, loc_data: Dict):
        """Draw blocked direction ranges as wedges"""
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

            # Convert to radians (pygame uses radians, 0 = right, CCW)
            # Our system: 0 = North (up), CW
            # Pygame: 0 = East (right), CCW
            # Conversion: pygame_rad = -((our_deg - 90) * π/180)
            start_angle = math.radians(-(from_deg - 90))
            end_angle = math.radians(-(to_deg - 90))

            # Create surface with alpha
            surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            rect = surf.get_rect(center=(int(radius), int(radius)))

            # Draw wedge
            pygame.draw.arc(surf, self.COLOR_BLOCKED, rect,
                          end_angle, start_angle, int(radius))

            # Draw filled sector
            points = [(int(radius), int(radius))]
            for angle in [start_angle, end_angle]:
                px = int(radius + radius * math.cos(angle))
                py = int(radius + radius * math.sin(angle))
                points.append((px, py))

            if len(points) > 2:
                pygame.draw.polygon(surf, self.COLOR_BLOCKED, points)

            # Blit to screen
            self.screen.blit(surf, (x - int(radius), y - int(radius)))

    def draw_locations(self):
        """Draw location markers with diameter"""
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_location = None

        for loc_name, loc_data in self.locations.items():
            coords = loc_data.get('coordinates')
            if not coords:
                continue

            x, y = self.world_to_screen(coords['x'], coords['y'])

            # Get diameter in meters (default 10m)
            diameter_meters = loc_data.get('diameter_meters', 10)
            # Convert to screen radius
            radius_screen = (diameter_meters / 2) * self.zoom

            # Skip if off-screen (with generous margin)
            margin = radius_screen + 100
            if x < -margin or x > self.width + margin or y < -margin or y > self.height + margin:
                continue

            # Draw blocked ranges
            self.draw_blocked_ranges(loc_name, loc_data)

            # Determine if waypoint
            is_waypoint = loc_data.get('is_waypoint', False)

            # Determine color
            is_current = (loc_name == self.current_location)
            is_selected = (loc_name == self.selected_location)
            is_hovered = False

            # Check if mouse is over this location (using real radius)
            dist = math.sqrt((mouse_pos[0] - x)**2 + (mouse_pos[1] - y)**2)
            if dist < radius_screen:
                is_hovered = True
                self.hovered_location = loc_name

            # Waypoints — оранжевые треугольники
            if is_waypoint:
                color = (255, 150, 0)  # Orange
                size = max(8, int(radius_screen))

                # Рисуем треугольник
                triangle_points = [
                    (x, y - size),          # Top
                    (x - size, y + size),   # Bottom-left
                    (x + size, y + size)    # Bottom-right
                ]

                # Outer ring if hovered
                if is_hovered or is_selected or is_current:
                    pygame.draw.polygon(self.screen, self.COLOR_HIGHLIGHT, [
                        (x, y - size - 4),
                        (x - size - 4, y + size + 4),
                        (x + size + 4, y + size + 4)
                    ], 2)

                # Fill + border
                pygame.draw.polygon(self.screen, color, triangle_points)
                pygame.draw.polygon(self.screen, (200, 100, 0), triangle_points, 2)
            else:
                # Обычные локации — круги
                color = self.COLOR_PLAYER if is_current else self.COLOR_LOCATION
                if is_selected:
                    color = self.COLOR_HIGHLIGHT

                # Draw outer ring if hovered or selected
                if is_hovered or is_selected:
                    pygame.draw.circle(self.screen, self.COLOR_HIGHLIGHT, (x, y),
                                     int(radius_screen + 6), 2)

                # Draw location circle (filled with alpha)
                surf = pygame.Surface((int(radius_screen * 2), int(radius_screen * 2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, 100),
                                 (int(radius_screen), int(radius_screen)),
                                 int(radius_screen))
                self.screen.blit(surf, (x - int(radius_screen), y - int(radius_screen)))

                # Draw border
                pygame.draw.circle(self.screen, color, (x, y), int(radius_screen), 2)

            # Draw label with diameter info
            label_text = f"{loc_name} ({diameter_meters}m)"
            label = self.font.render(label_text, True, self.COLOR_TEXT)
            label_rect = label.get_rect(center=(x, y - radius_screen - 15))
            # Shadow
            shadow = self.font.render(label_text, True, (0, 0, 0))
            self.screen.blit(shadow, (label_rect.x + 1, label_rect.y + 1))
            self.screen.blit(label, label_rect)

    def draw_ui(self):
        """Draw UI overlay"""
        # Campaign name
        campaign_name = self.overview.get('campaign_name', 'Campaign Map')
        title = self.font_large.render(campaign_name, True, self.COLOR_TEXT)
        self.screen.blit(title, (10, 10))

        # Instructions
        instructions = [
            "Controls:",
            "  Mouse Wheel - Zoom",
            "  Click+Drag - Pan",
            "  Click Location - Select",
            "  ESC - Exit",
            "  R - Reload Data"
        ]

        y_offset = 40
        for line in instructions:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

        # Terrain legend
        y_offset += 10
        legend_text = self.font.render("Terrain Types:", True, self.COLOR_TEXT)
        self.screen.blit(legend_text, (10, y_offset))
        y_offset += 20

        for terrain, color in self.TERRAIN_COLORS.items():
            if terrain == 'default':
                continue
            # Draw colored line
            pygame.draw.line(self.screen, color, (15, y_offset + 5), (35, y_offset + 5), 3)
            # Draw text
            text = self.font.render(terrain, True, color)
            self.screen.blit(text, (40, y_offset))
            y_offset += 18

        # Camera info
        info_lines = [
            f"Zoom: {self.zoom:.2f}x",
            f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})"
        ]

        y_offset = self.height - 60
        for line in info_lines:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

        # Location colors legend
        legend_items = [
            (self.COLOR_PLAYER, "@ Current Position"),
            (self.COLOR_LOCATION, "● Location")
        ]
        for color, label in legend_items:
            # Draw colored circle
            pygame.draw.circle(self.screen, color, (15, y_offset + 5), 5)
            # Draw text
            text = self.font.render(label, True, self.COLOR_TEXT)
            self.screen.blit(text, (25, y_offset))
            y_offset += 18

        # Selected location info
        if self.selected_location and self.selected_location in self.locations:
            self.draw_location_panel(self.selected_location)

    def draw_location_panel(self, loc_name: str):
        """Draw info panel for selected location"""
        loc_data = self.locations[loc_name]
        coords = loc_data.get('coordinates', {})

        panel_width = 400
        panel_height = 300
        panel_x = self.width - panel_width - 10
        panel_y = 10

        # Background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, self.COLOR_TEXT, panel_rect, 2)

        # Title
        title = self.font_large.render(loc_name, True, self.COLOR_HIGHLIGHT)
        self.screen.blit(title, (panel_x + 10, panel_y + 10))

        # Info
        y = panel_y + 40
        info_lines = [
            f"Position: {loc_data.get('position', 'unknown')}",
            f"Coordinates: ({coords.get('x', 0)}, {coords.get('y', 0)})",
            f"",
            "Connections:"
        ]

        for conn in loc_data.get('connections', []):
            to_loc = conn.get('to', 'unknown')
            dist = conn.get('distance_meters', 0)
            bearing = conn.get('bearing', 0)
            info_lines.append(f"  → {to_loc} ({dist}m, {bearing}°)")

        # Blocked ranges
        blocked = loc_data.get('blocked_ranges', [])
        if blocked:
            info_lines.append("")
            info_lines.append("Blocked Directions:")
            for block in blocked:
                info_lines.append(f"  {block['from']}°-{block['to']}°: {block['reason']}")

        for line in info_lines:
            if y > panel_y + panel_height - 20:
                break
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (panel_x + 10, y))
            y += 18

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    self.reload_data()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.hovered_location:
                        self.selected_location = self.hovered_location
                    else:
                        self.dragging = True
                        self.drag_start = event.pos

                elif event.button == 4:  # Scroll up (zoom in)
                    old_zoom = self.zoom
                    self.zoom = min(self.zoom * 1.1, self.max_zoom)
                    # Zoom towards mouse
                    mx, my = pygame.mouse.get_pos()
                    world_pos = self.screen_to_world(mx, my)
                    # Adjust camera to keep mouse over same world position
                    new_screen = self.world_to_screen(world_pos[0], world_pos[1])
                    world_offset_x = (new_screen[0] - mx) / self.zoom
                    world_offset_y = (my - new_screen[1]) / self.zoom
                    self.camera_x += world_offset_x
                    self.camera_y += world_offset_y

                elif event.button == 5:  # Scroll down (zoom out)
                    old_zoom = self.zoom
                    self.zoom = max(self.zoom / 1.1, self.min_zoom)
                    mx, my = pygame.mouse.get_pos()
                    world_pos = self.screen_to_world(mx, my)
                    new_screen = self.world_to_screen(world_pos[0], world_pos[1])
                    world_offset_x = (new_screen[0] - mx) / self.zoom
                    world_offset_y = (my - new_screen[1]) / self.zoom
                    self.camera_x += world_offset_x
                    self.camera_y += world_offset_y

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
        """Main render loop"""
        running = True

        while running:
            running = self.handle_events()

            # Clear screen
            self.screen.fill(self.COLOR_BG)

            # Draw terrain background (Voronoi, each frame)
            self.draw_terrain_background()

            # Draw map elements
            self.draw_grid()
            self.draw_connections()
            self.draw_locations()

            # Draw UI overlay
            self.draw_ui()

            # Update display
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def main():
    """CLI interface for GUI map"""
    import argparse

    parser = argparse.ArgumentParser(description='Interactive campaign map')
    parser.add_argument('--width', type=int, default=1200, help='Window width')
    parser.add_argument('--height', type=int, default=800, help='Window height')

    args = parser.parse_args()

    # Determine campaign directory
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
