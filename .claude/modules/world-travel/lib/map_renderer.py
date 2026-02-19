#!/usr/bin/env python3
"""
ASCII map renderer for location visualization
Renders campaign maps with locations, connections, and current position
"""

import sys
import math
from typing import Dict, List, Tuple, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.json_ops import JsonOperations
from connection_utils import get_unique_edges


class MapRenderer:
    """Renders ASCII maps of campaign locations"""

    # Map symbols
    SYMBOLS = {
        'player': '@',
        'location': '●',
        'connection': '─',
        'vertical': '│',
        'corner_ne': '╮',
        'corner_nw': '╭',
        'corner_se': '╯',
        'corner_sw': '╰',
        'cross': '┼',
        'fog': '▓',
        'empty': ' '
    }

    # Compass rose
    COMPASS = {
        'n': '↑',
        's': '↓',
        'e': '→',
        'w': '←',
        'ne': '↗',
        'nw': '↖',
        'se': '↘',
        'sw': '↙'
    }

    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'gray': '\033[90m',
        'bright_green': '\033[92m',
        'bright_blue': '\033[94m',
        'bright_yellow': '\033[93m'
    }

    # Terrain colors
    TERRAIN_COLORS = {
        'forest': 'green',
        'open': 'white',
        'water': 'blue',
        'swamp': 'cyan',
        'desert': 'yellow',
        'mountain': 'gray',
        'default': 'white'
    }

    def __init__(self, campaign_dir: str):
        self.json_ops = JsonOperations(campaign_dir)

    def colorize(self, text: str, color_name: str, use_colors: bool = True) -> str:
        """Apply ANSI color to text"""
        if not use_colors:
            return text
        color_code = self.COLORS.get(color_name, '')
        reset = self.COLORS['reset']
        return f"{color_code}{text}{reset}"

    def _get_stable_color_for_location(self, loc_name: str) -> str:
        """Generate stable unique color for location based on name hash"""
        # Hash location name to get consistent color
        import hashlib
        hash_val = int(hashlib.md5(loc_name.encode()).hexdigest()[:8], 16)

        # Pick from available colors (excluding gray/white for better visibility)
        color_pool = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan',
                     'bright_green', 'bright_blue', 'bright_yellow']
        return color_pool[hash_val % len(color_pool)]

    def _get_terrain_color(self, terrain: str) -> str:
        """Get color for terrain type"""
        terrain_colors = {
            'forest': 'green',
            'open': 'white',
            'water': 'blue',
            'swamp': 'cyan',
            'desert': 'yellow',
            'mountain': 'gray',
            'default': 'white'
        }
        return terrain_colors.get(terrain, 'white')

    def _colorize_map_line(self, line: str) -> str:
        """Apply colors to a single map line (fallback for simple coloring)"""
        # Player symbol - red
        line = line.replace(self.SYMBOLS['player'],
                          self.colorize(self.SYMBOLS['player'], 'red'))

        # Location symbol - cyan (will be overridden by metadata-based coloring)
        line = line.replace(self.SYMBOLS['location'],
                          self.colorize(self.SYMBOLS['location'], 'cyan'))

        # Connections - green (will be overridden by terrain-based coloring)
        line = line.replace(self.SYMBOLS['connection'],
                          self.colorize(self.SYMBOLS['connection'], 'green'))
        line = line.replace(self.SYMBOLS['vertical'],
                          self.colorize(self.SYMBOLS['vertical'], 'green'))

        return line

    def render_map(self, width: int = 80, height: int = 40,
                  show_labels: bool = True, show_compass: bool = True,
                  use_colors: bool = False) -> str:
        """
        Render ASCII map of all discovered locations

        Args:
            width: Map width in characters
            height: Map height in characters
            show_labels: Show location names
            show_compass: Show compass rose
            use_colors: Use ANSI colors for terrain and locations

        Returns:
            ASCII art string of the map
        """
        # Load data
        locations = self.json_ops.load_json("locations.json") or {}
        overview = self.json_ops.load_json("campaign-overview.json") or {}

        if not locations:
            return "[ERROR] No locations found"

        # Get current location
        current_loc = overview.get('player_position', {}).get('current_location')

        # Calculate bounds
        coords_list = []
        for loc_data in locations.values():
            coords = loc_data.get('coordinates')
            if coords:
                coords_list.append((coords['x'], coords['y']))

        if not coords_list:
            return "[ERROR] No location coordinates found"

        min_x = min(c[0] for c in coords_list)
        max_x = max(c[0] for c in coords_list)
        min_y = min(c[0] for c in coords_list)
        max_y = max(c[1] for c in coords_list)

        # Add padding
        padding = 500
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding

        # Create grid and metadata grid
        grid = [[self.SYMBOLS['empty'] for _ in range(width)] for _ in range(height)]
        # metadata_grid stores: {'type': 'connection'/'location'/'player', 'data': terrain/loc_name}
        metadata_grid = [[None for _ in range(width)] for _ in range(height)]

        # Scale coordinates to grid
        def scale_coord(x: float, y: float) -> Tuple[int, int]:
            # Invert Y for screen coordinates (top = higher Y)
            gx = int((x - min_x) / (max_x - min_x) * (width - 10)) + 5
            gy = int((max_y - y) / (max_y - min_y) * (height - 5)) + 2
            return gx, gy

        # Draw connections first (so they appear under locations)
        for loc_a, loc_b, conn in get_unique_edges(locations):
            coords_a = locations[loc_a].get('coordinates')
            coords_b = locations.get(loc_b, {}).get('coordinates')
            if not coords_a or not coords_b:
                continue

            x1, y1 = scale_coord(coords_a['x'], coords_a['y'])
            x2, y2 = scale_coord(coords_b['x'], coords_b['y'])
            terrain = conn.get('terrain', 'default')

            self._draw_line(grid, metadata_grid, x1, y1, x2, y2, terrain)

        # Draw locations
        location_positions = {}
        for loc_name, loc_data in locations.items():
            coords = loc_data.get('coordinates')
            if not coords:
                continue

            gx, gy = scale_coord(coords['x'], coords['y'])

            # Check bounds
            if 0 <= gx < width and 0 <= gy < height:
                # Draw symbol
                if loc_name == current_loc:
                    grid[gy][gx] = self.SYMBOLS['player']
                    metadata_grid[gy][gx] = {'type': 'player', 'location': loc_name}
                else:
                    grid[gy][gx] = self.SYMBOLS['location']
                    metadata_grid[gy][gx] = {'type': 'location', 'location': loc_name}

                location_positions[loc_name] = (gx, gy)

        # Build output
        lines = []

        # Title
        campaign_name = overview.get('campaign_name', 'Campaign Map')
        lines.append("=" * width)
        lines.append(f"  {campaign_name}".ljust(width))
        lines.append("=" * width)

        # Grid - build with colors from metadata
        for y, row in enumerate(grid):
            line_chars = []
            for x, char in enumerate(row):
                if use_colors and metadata_grid[y][x]:
                    meta = metadata_grid[y][x]
                    if meta['type'] == 'player':
                        # Player - always red
                        line_chars.append(self.colorize(char, 'red'))
                    elif meta['type'] == 'location':
                        # Location - unique color based on name
                        loc_color = self._get_stable_color_for_location(meta['location'])
                        line_chars.append(self.colorize(char, loc_color))
                    elif meta['type'] == 'connection':
                        # Connection - color based on terrain
                        terrain_color = self._get_terrain_color(meta['terrain'])
                        line_chars.append(self.colorize(char, terrain_color))
                    else:
                        line_chars.append(char)
                else:
                    line_chars.append(char)
            lines.append(''.join(line_chars))

        # Legend
        lines.append("=" * width)
        legend_items = [
            f"{self.SYMBOLS['player']} = Current location",
            f"{self.SYMBOLS['location']} = Location",
            f"{self.SYMBOLS['connection']} = Connection"
        ]
        lines.append("  Legend: " + "  |  ".join(legend_items))

        # Compass rose
        if show_compass:
            compass_lines = [
                f"      {self.COMPASS['n']}",
                f"    {self.COMPASS['nw']} + {self.COMPASS['ne']}",
                f"    {self.COMPASS['w']} + {self.COMPASS['e']}",
                f"    {self.COMPASS['sw']} + {self.COMPASS['se']}",
                f"      {self.COMPASS['s']}"
            ]
            lines.append("")
            lines.extend(compass_lines)

        # Location labels
        if show_labels:
            lines.append("")
            lines.append("Locations:")
            for loc_name, (gx, gy) in sorted(location_positions.items()):
                if loc_name == current_loc:
                    symbol = self.SYMBOLS['player']
                    if use_colors:
                        symbol = self.colorize(symbol, 'red')
                        loc_display = self.colorize(loc_name, 'red')
                    else:
                        loc_display = loc_name
                else:
                    symbol = self.SYMBOLS['location']
                    if use_colors:
                        loc_color = self._get_stable_color_for_location(loc_name)
                        symbol = self.colorize(symbol, loc_color)
                        loc_display = self.colorize(loc_name, loc_color)
                    else:
                        loc_display = loc_name
                lines.append(f"  {symbol} {loc_display}")

        lines.append("=" * width)

        return '\n'.join(lines)

    def _draw_line(self, grid: List[List[str]], metadata_grid: List[List],
                   x1: int, y1: int, x2: int, y2: int, terrain: str = 'default'):
        """
        Draw line between two points using Bresenham's algorithm
        """
        height = len(grid)
        width = len(grid[0]) if grid else 0

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1

        while True:
            # Don't overwrite location symbols
            if 0 <= x < width and 0 <= y < height:
                if grid[y][x] not in [self.SYMBOLS['player'], self.SYMBOLS['location']]:
                    # Choose connection symbol based on direction
                    if abs(dx) > abs(dy):
                        grid[y][x] = self.SYMBOLS['connection']
                    else:
                        grid[y][x] = self.SYMBOLS['vertical']
                    # Store metadata
                    metadata_grid[y][x] = {'type': 'connection', 'terrain': terrain}

            if x == x2 and y == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def render_minimap(self, radius: int = 5) -> str:
        """
        Render small mini-map showing only nearby locations

        Args:
            radius: Number of grid cells around player to show (max 50)

        Returns:
            ASCII minimap string
        """
        # Validate and clamp radius
        MAX_RADIUS = 50
        if radius < 1:
            radius = 1
        elif radius > MAX_RADIUS:
            print(f"[WARNING] Radius {radius} too large, clamping to {MAX_RADIUS}")
            radius = MAX_RADIUS

        # Load data
        locations = self.json_ops.load_json("locations.json") or {}
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        current_loc = overview.get('player_position', {}).get('current_location')

        if not current_loc or current_loc not in locations:
            return "[ERROR] Current location not found"

        current_coords = locations[current_loc].get('coordinates')
        if not current_coords:
            return "[ERROR] Current location has no coordinates"

        # Simple radius-based minimap
        size = radius * 2 + 1
        center = radius
        grid = [[self.SYMBOLS['fog'] for _ in range(size)] for _ in range(size)]

        # Center is player (set after creating grid)
        grid[center][center] = self.SYMBOLS['player']

        # Find nearby locations
        for loc_name, loc_data in locations.items():
            if loc_name == current_loc:
                continue

            coords = loc_data.get('coordinates')
            if not coords:
                continue

            # Calculate relative position
            dx = coords['x'] - current_coords['x']
            dy = coords['y'] - current_coords['y']
            distance = math.sqrt(dx**2 + dy**2)

            # Scale to minimap (1000m per cell)
            scale = 1000
            gx = center + int(round(dx / scale))
            gy = center - int(round(dy / scale))  # Invert Y

            # Check bounds and don't overwrite player
            if 0 <= gx < size and 0 <= gy < size:
                if grid[gy][gx] != self.SYMBOLS['player']:
                    grid[gy][gx] = self.SYMBOLS['location']

        # Build output
        lines = ["╔" + "═" * size + "╗"]
        for row in grid:
            lines.append("║" + ''.join(row) + "║")
        lines.append("╚" + "═" * size + "╝")
        lines.append(f"  {self.SYMBOLS['player']} = You ({current_loc})")
        lines.append(f"  {self.SYMBOLS['location']} = Location")
        lines.append(f"  Scale: ~1km per cell")

        return '\n'.join(lines)


def main():
    """CLI interface for map rendering"""
    import argparse

    parser = argparse.ArgumentParser(description='Render campaign map')
    parser.add_argument('--width', type=int, default=80, help='Map width')
    parser.add_argument('--height', type=int, default=40, help='Map height')
    parser.add_argument('--no-labels', action='store_true', help='Hide location labels')
    parser.add_argument('--no-compass', action='store_true', help='Hide compass rose')
    parser.add_argument('--minimap', action='store_true', help='Render minimap instead')
    parser.add_argument('--radius', type=int, default=5, help='Minimap radius')
    parser.add_argument('--color', action='store_true', help='Use ANSI colors')

    args = parser.parse_args()

    # Determine campaign directory
    import os
    active_campaign_file = Path("world-state/active-campaign.txt")
    if not active_campaign_file.exists():
        print("[ERROR] No active campaign")
        sys.exit(1)

    active_campaign = active_campaign_file.read_text().strip()
    campaign_dir = Path(f"world-state/campaigns/{active_campaign}")

    renderer = MapRenderer(str(campaign_dir))

    if args.minimap:
        print(renderer.render_minimap(radius=args.radius))
    else:
        print(renderer.render_map(
            width=args.width,
            height=args.height,
            show_labels=not args.no_labels,
            show_compass=not args.no_compass,
            use_colors=args.color
        ))


if __name__ == "__main__":
    main()
