#!/usr/bin/env python3
"""
Pathfinding and coordinate calculations for location navigation
Handles intelligent route finding, bearing calculations, and coordinate systems
"""

import math
import sys
from typing import Dict, List, Optional, Tuple
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from connection_utils import get_connections as cu_get_connections


class PathFinder:
    """Pathfinding and coordinate calculations for locations"""

    # Compass directions with degree ranges
    COMPASS_DIRECTIONS = [
        (0, "Север", "N"),
        (22.5, "ССВ", "NNE"),
        (45, "СВ", "NE"),
        (67.5, "ВСВ", "ENE"),
        (90, "Восток", "E"),
        (112.5, "ВЮВ", "ESE"),
        (135, "ЮВ", "SE"),
        (157.5, "ЮЮВ", "SSE"),
        (180, "Юг", "S"),
        (202.5, "ЮЮЗ", "SSW"),
        (225, "ЮЗ", "SW"),
        (247.5, "ЗЮЗ", "WSW"),
        (270, "Запад", "W"),
        (292.5, "ЗСЗ", "WNW"),
        (315, "СЗ", "NW"),
        (337.5, "ССЗ", "NNW")
    ]

    @staticmethod
    def calculate_coordinates(from_coords: Dict[str, float], distance: float, bearing: float) -> Dict[str, float]:
        """
        Calculate destination coordinates from distance + bearing

        Args:
            from_coords: {"x": 0, "y": 0} starting point
            distance: distance in meters
            bearing: direction in degrees (0=North, 90=East, 180=South, 270=West)

        Returns:
            {"x": float, "y": float} destination coordinates
        """
        rad = math.radians(bearing)

        # Calculate offset
        # sin(bearing) gives x-component (East/West)
        # cos(bearing) gives y-component (North/South)
        dx = distance * math.sin(rad)
        dy = distance * math.cos(rad)

        return {
            "x": round(from_coords["x"] + dx),
            "y": round(from_coords["y"] + dy)
        }

    @staticmethod
    def calculate_direct_distance(coord_a: Dict[str, float], coord_b: Dict[str, float]) -> float:
        """
        Calculate straight-line distance between two points (Euclidean distance)

        Args:
            coord_a: {"x": 0, "y": 0}
            coord_b: {"x": 100, "y": 100}

        Returns:
            Distance in meters
        """
        dx = coord_b["x"] - coord_a["x"]
        dy = coord_b["y"] - coord_a["y"]

        return round(math.sqrt(dx**2 + dy**2))

    @staticmethod
    def calculate_bearing(coord_a: Dict[str, float], coord_b: Dict[str, float]) -> float:
        """
        Calculate bearing (direction) from A to B in degrees

        Args:
            coord_a: {"x": 0, "y": 0} starting point
            coord_b: {"x": 100, "y": 100} destination

        Returns:
            Bearing in degrees (0-360, where 0=North)
        """
        dx = coord_b["x"] - coord_a["x"]
        dy = coord_b["y"] - coord_a["y"]

        # atan2 returns radians from -π to π
        rad = math.atan2(dx, dy)

        # Convert to degrees (0-360)
        degrees = math.degrees(rad)
        if degrees < 0:
            degrees += 360

        return round(degrees, 1)

    @staticmethod
    def bearing_to_compass(bearing: float) -> Tuple[str, str]:
        """
        Convert bearing degrees to compass direction

        Args:
            bearing: degrees (0-360)

        Returns:
            Tuple of (Russian name, English abbreviation)
            Example: (315) -> ("Северо-Запад", "NW")
        """
        # Normalize bearing to 0-360
        bearing = bearing % 360

        # Find closest direction
        closest_idx = round(bearing / 22.5) % 16

        return (
            PathFinder.COMPASS_DIRECTIONS[closest_idx][1],
            PathFinder.COMPASS_DIRECTIONS[closest_idx][2]
        )

    @staticmethod
    def find_route(from_loc: str, to_loc: str, locations: Dict) -> Dict:
        """
        Find shortest route between locations using BFS

        Args:
            from_loc: Starting location name
            to_loc: Destination location name
            locations: Full locations dict from locations.json

        Returns:
            {
                "found": True/False,
                "path": ["Location A", "Location B", "Location C"],
                "distance": 3000,
                "hops": 2
            }
        """
        if from_loc not in locations or to_loc not in locations:
            return {"found": False}

        # BFS to find shortest path
        queue = deque([(from_loc, [from_loc], 0)])
        visited = set()

        while queue:
            current, path, distance = queue.popleft()

            # Found destination
            if current == to_loc:
                return {
                    "found": True,
                    "path": path,
                    "distance": distance,
                    "hops": len(path) - 1
                }

            # Skip if already visited
            if current in visited:
                continue
            visited.add(current)

            # Explore connections
            for conn in cu_get_connections(current, locations):
                next_loc = conn.get("to")
                conn_distance = conn.get("distance_meters", 0)

                # Only follow connections with valid distance
                if next_loc and conn_distance > 0 and next_loc not in visited:
                    queue.append((
                        next_loc,
                        path + [next_loc],
                        distance + conn_distance
                    ))

        # No route found
        return {"found": False}

    @staticmethod
    def is_bearing_blocked(location_data: Dict, bearing: float, tolerance: float = 5) -> Tuple[bool, Optional[str]]:
        """
        Check if a bearing is blocked by terrain/obstacles

        Args:
            location_data: Location dict containing blocked_ranges
            bearing: Direction in degrees to check
            tolerance: Additional degrees to check around the exact bearing

        Returns:
            (is_blocked, reason) tuple
        """
        blocked_ranges = location_data.get("blocked_ranges", [])

        # Normalize bearing to 0-360
        bearing = bearing % 360

        for block in blocked_ranges:
            from_deg = block["from"]
            to_deg = block["to"]
            reason = block.get("reason", "Blocked")

            # Handle wrap-around (e.g., 350° to 10°)
            if from_deg > to_deg:
                # Range crosses 0° (North)
                if bearing >= from_deg or bearing <= to_deg:
                    return True, reason
            else:
                # Normal range
                if from_deg <= bearing <= to_deg:
                    return True, reason

            # Check tolerance range (bearing ± tolerance)
            for offset in [-tolerance, tolerance]:
                test_bearing = (bearing + offset) % 360

                if from_deg > to_deg:
                    if test_bearing >= from_deg or test_bearing <= to_deg:
                        return True, f"{reason} (близко к заблокированному направлению)"
                else:
                    if from_deg <= test_bearing <= to_deg:
                        return True, f"{reason} (близко к заблокированному направлению)"

        return False, None

    @staticmethod
    def find_all_routes(from_loc: str, to_loc: str, locations: Dict, max_routes: int = 5) -> List[Dict]:
        """
        Find all possible routes between locations (up to max_routes)

        Args:
            from_loc: Starting location
            to_loc: Destination
            locations: Full locations dict
            max_routes: Maximum number of routes to return

        Returns:
            List of route dicts sorted by distance (shortest first)
            Each route includes: path, distance, hops, terrains (list of terrain types per hop)
        """
        if from_loc not in locations or to_loc not in locations:
            return []

        all_routes = []
        queue = deque([(from_loc, [from_loc], 0, set(), [])])  # Added terrains list

        while queue and len(all_routes) < max_routes:
            current, path, distance, visited_edges, terrains = queue.popleft()

            # Found destination - save this route
            if current == to_loc:
                all_routes.append({
                    "path": path,
                    "distance": distance,
                    "hops": len(path) - 1,
                    "terrains": terrains  # List of terrain types for each hop
                })
                continue

            # Explore connections
            for conn in cu_get_connections(current, locations):
                next_loc = conn.get("to")
                conn_distance = conn.get("distance_meters", 0)
                conn_terrain = conn.get("terrain", "open")  # Get terrain type

                # Create edge identifier
                edge = tuple(sorted([current, next_loc]))

                # Avoid revisiting same edge and loops
                if (next_loc and
                    conn_distance > 0 and
                    next_loc not in path and  # No loops
                    edge not in visited_edges):

                    new_visited = visited_edges | {edge}
                    queue.append((
                        next_loc,
                        path + [next_loc],
                        distance + conn_distance,
                        new_visited,
                        terrains + [conn_terrain]  # Append terrain for this hop
                    ))

        # Sort by distance (shortest first)
        all_routes.sort(key=lambda r: r["distance"])

        return all_routes

    @staticmethod
    def get_reverse_bearing(bearing: float) -> float:
        """
        Get the opposite bearing (for bidirectional connections)

        Args:
            bearing: Original bearing in degrees

        Returns:
            Reverse bearing (bearing + 180) normalized to 0-360
        """
        return (bearing + 180) % 360


if __name__ == "__main__":
    # Test calculations
    pf = PathFinder()

    # Test 1: Calculate coordinates
    start = {"x": 0, "y": 0}
    coords_ne = pf.calculate_coordinates(start, 1000, 45)  # Northeast 1km
    print(f"Northeast 1km from origin: {coords_ne}")

    # Test 2: Calculate bearing
    bearing = pf.calculate_bearing(start, coords_ne)
    print(f"Bearing from origin to NE point: {bearing}°")

    # Test 3: Compass direction
    direction, abbr = pf.bearing_to_compass(bearing)
    print(f"Direction: {direction} ({abbr})")

    # Test 4: Direct distance
    distance = pf.calculate_direct_distance(start, coords_ne)
    print(f"Distance: {distance}m")

    # Test 5: Blocked check
    location_data = {
        "blocked_ranges": [
            {"from": 160, "to": 200, "reason": "Обрыв"}
        ]
    }
    is_blocked, reason = pf.is_bearing_blocked(location_data, 180)
    print(f"180° blocked: {is_blocked} ({reason})")
