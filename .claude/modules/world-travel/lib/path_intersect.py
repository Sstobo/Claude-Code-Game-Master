#!/usr/bin/env python3
"""
Path intersection detection for location routing
Checks if a path between two locations intersects any intermediate locations
"""

import math
from typing import List, Tuple, Dict, Optional


def point_to_segment_distance(px: float, py: float,
                              x1: float, y1: float,
                              x2: float, y2: float) -> float:
    """
    Calculate shortest distance from point (px, py) to line segment (x1,y1)-(x2,y2)
    Returns distance in same units as input coordinates
    """
    # Vector from start to end of segment
    dx = x2 - x1
    dy = y2 - y1

    # Handle zero-length segment
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)

    # Calculate parameter t for closest point on infinite line
    # Project point onto line: t = dot((P-A), (B-A)) / ||B-A||^2
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)

    # Clamp t to [0, 1] to stay on segment
    t = max(0, min(1, t))

    # Find closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Return distance to closest point
    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)


def check_path_intersection(start_name: str, end_name: str,
                           locations: Dict,
                           threshold_buffer: float = 1.0) -> List[str]:
    """
    Check if direct path from start to end intersects any other locations

    Args:
        start_name: Starting location name
        end_name: Ending location name
        locations: Dict of all locations with coordinates and diameter_meters
        threshold_buffer: Multiplier for diameter (1.0 = touching, >1.0 = must pass through)

    Returns:
        List of location names that the path intersects (excluding start and end)
    """
    if start_name not in locations or end_name not in locations:
        return []

    start_coords = locations[start_name].get('coordinates')
    end_coords = locations[end_name].get('coordinates')

    if not start_coords or not end_coords:
        return []

    x1, y1 = start_coords['x'], start_coords['y']
    x2, y2 = end_coords['x'], end_coords['y']

    intersecting = []

    for loc_name, loc_data in locations.items():
        # Skip start and end locations
        if loc_name == start_name or loc_name == end_name:
            continue

        coords = loc_data.get('coordinates')
        if not coords:
            continue

        px, py = coords['x'], coords['y']
        diameter = loc_data.get('diameter_meters', 10)
        radius = diameter / 2

        # Calculate distance from location center to path line segment
        dist = point_to_segment_distance(px, py, x1, y1, x2, y2)

        # Check if path passes through location (within radius * buffer)
        if dist <= radius * threshold_buffer:
            intersecting.append(loc_name)

    return intersecting


def find_route_with_waypoints(start_name: str, end_name: str,
                              locations: Dict) -> List[str]:
    """
    Find route from start to end, adding waypoints for any intersected locations

    Returns:
        List of location names forming the route [start, waypoint1, waypoint2, ..., end]
    """
    # Check direct path
    intersections = check_path_intersection(start_name, end_name, locations)

    if not intersections:
        # Direct path is clear
        return [start_name, end_name]

    # Path intersects locations - need to route through them
    # Build route by ordering intersected locations by distance from start
    start_coords = locations[start_name]['coordinates']
    start_x, start_y = start_coords['x'], start_coords['y']

    # Calculate distance from start for each intersection
    waypoints_with_dist = []
    for loc_name in intersections:
        coords = locations[loc_name]['coordinates']
        dx = coords['x'] - start_x
        dy = coords['y'] - start_y
        dist = math.sqrt(dx*dx + dy*dy)
        waypoints_with_dist.append((dist, loc_name))

    # Sort by distance from start
    waypoints_with_dist.sort()
    waypoints = [name for _, name in waypoints_with_dist]

    # Build final route
    return [start_name] + waypoints + [end_name]


if __name__ == "__main__":
    # Test with sample data
    test_locations = {
        "A": {"coordinates": {"x": 0, "y": 0}, "diameter_meters": 100},
        "B": {"coordinates": {"x": 1000, "y": 0}, "diameter_meters": 100},
        "C": {"coordinates": {"x": 500, "y": 50}, "diameter_meters": 150},  # Should intersect A-B
        "D": {"coordinates": {"x": 500, "y": 500}, "diameter_meters": 50},  # Should NOT intersect
    }

    print("Testing path intersection detection:")
    print(f"A -> B intersections: {check_path_intersection('A', 'B', test_locations)}")
    print(f"A -> D intersections: {check_path_intersection('A', 'D', test_locations)}")

    print(f"\nRoute A -> B: {find_route_with_waypoints('A', 'B', test_locations)}")
    print(f"Route A -> D: {find_route_with_waypoints('A', 'D', test_locations)}")
