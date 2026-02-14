#!/usr/bin/env python3
"""
Automatic path splitting through intersecting locations
Splits long paths into multiple segments when they pass through intermediate locations
"""

import json
import math
from typing import Dict, List, Tuple
from pathlib import Path
from path_intersect import check_path_intersection


def calculate_bearing(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate bearing from point 1 to point 2 (0° = North, clockwise)"""
    dx = x2 - x1
    dy = y2 - y1
    angle_rad = math.atan2(dx, dy)
    bearing = math.degrees(angle_rad)
    return bearing % 360


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def connection_exists(from_loc: str, to_loc: str, locations: Dict) -> bool:
    """Check if connection already exists from_loc → to_loc"""
    if from_loc not in locations:
        return False

    connections = locations[from_loc].get('connections', [])
    return any(conn.get('to') == to_loc for conn in connections)


def add_connection(from_loc: str, to_loc: str, locations: Dict, terrain: str = 'open'):
    """Add bidirectional connection between two locations if it doesn't exist"""
    if from_loc not in locations or to_loc not in locations:
        return

    from_coords = locations[from_loc]['coordinates']
    to_coords = locations[to_loc]['coordinates']

    # Calculate distance and bearing
    distance = calculate_distance(
        from_coords['x'], from_coords['y'],
        to_coords['x'], to_coords['y']
    )
    bearing_forward = calculate_bearing(
        from_coords['x'], from_coords['y'],
        to_coords['x'], to_coords['y']
    )
    bearing_backward = calculate_bearing(
        to_coords['x'], to_coords['y'],
        from_coords['x'], from_coords['y']
    )

    # Add forward connection if doesn't exist
    if not connection_exists(from_loc, to_loc, locations):
        if 'connections' not in locations[from_loc]:
            locations[from_loc]['connections'] = []

        locations[from_loc]['connections'].append({
            'to': to_loc,
            'path': f"{distance:.0f}m на {bearing_forward:.1f}°",
            'distance_meters': int(distance),
            'bearing': round(bearing_forward, 1),
            'terrain': terrain
        })
        print(f"   ✓ Added: {from_loc} → {to_loc} ({distance:.0f}m, {bearing_forward:.1f}°, {terrain})")

    # Add backward connection if doesn't exist
    if not connection_exists(to_loc, from_loc, locations):
        if 'connections' not in locations[to_loc]:
            locations[to_loc]['connections'] = []

        locations[to_loc]['connections'].append({
            'to': from_loc,
            'path': f"{distance:.0f}m на {bearing_backward:.1f}°",
            'distance_meters': int(distance),
            'bearing': round(bearing_backward, 1),
            'terrain': terrain
        })
        print(f"   ✓ Added: {to_loc} → {from_loc} ({distance:.0f}m, {bearing_backward:.1f}°, {terrain})")


def remove_connection(from_loc: str, to_loc: str, locations: Dict):
    """Remove connection from_loc → to_loc"""
    if from_loc not in locations:
        return

    connections = locations[from_loc].get('connections', [])
    original_len = len(connections)

    locations[from_loc]['connections'] = [
        conn for conn in connections if conn.get('to') != to_loc
    ]

    if len(locations[from_loc]['connections']) < original_len:
        print(f"   ✗ Removed: {from_loc} → {to_loc}")


def split_intersecting_paths(locations: Dict, dry_run: bool = False) -> Dict:
    """
    Split paths that intersect intermediate locations

    Args:
        locations: Dict of locations with coordinates and connections
        dry_run: If True, only report what would be changed without modifying

    Returns:
        Modified locations dict (or original if dry_run=True)
    """
    if dry_run:
        print("\n🔍 DRY RUN - No changes will be made\n")

    changes_made = False

    # Find all intersecting paths
    for loc_name in list(locations.keys()):
        loc_data = locations[loc_name]
        connections = loc_data.get('connections', [])

        for conn in list(connections):
            to_loc = conn.get('to')
            if not to_loc or to_loc not in locations:
                continue

            # Check for intersections
            intersections = check_path_intersection(loc_name, to_loc, locations)

            if not intersections:
                continue

            # Path intersects locations - need to split
            terrain = conn.get('terrain', 'open')

            print(f"\n📍 Splitting: {loc_name} → {to_loc}")
            print(f"   Passes through: {', '.join(intersections)}")

            if not dry_run:
                # Remove original long path (bidirectional)
                remove_connection(loc_name, to_loc, locations)
                remove_connection(to_loc, loc_name, locations)

                # Build route through waypoints
                route = [loc_name] + intersections + [to_loc]

                # Create connections for each segment
                for i in range(len(route) - 1):
                    from_point = route[i]
                    to_point = route[i + 1]
                    add_connection(from_point, to_point, locations, terrain)

                changes_made = True
            else:
                # Dry run - just show what would happen
                route = [loc_name] + intersections + [to_loc]
                print(f"   Would create route: {' → '.join(route)}")

                for i in range(len(route) - 1):
                    from_point = route[i]
                    to_point = route[i + 1]

                    if connection_exists(from_point, to_point, locations):
                        print(f"   ○ Keep existing: {from_point} → {to_point}")
                    else:
                        print(f"   + Would add: {from_point} → {to_point}")

    if not changes_made and not dry_run:
        print("\n✓ No intersecting paths found - all connections are already optimal")

    return locations


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Split intersecting paths')
    parser.add_argument('campaign_dir', help='Path to campaign directory')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--apply', action='store_true', help='Apply changes to locations.json')

    args = parser.parse_args()

    campaign_path = Path(args.campaign_dir)
    locations_file = campaign_path / 'locations.json'

    if not locations_file.exists():
        print(f"Error: {locations_file} not found")
        exit(1)

    # Load locations
    with open(locations_file) as f:
        locations = json.load(f)

    print(f"📂 Campaign: {campaign_path.name}")
    print(f"📍 Loaded {len(locations)} locations")
    print("=" * 60)

    # Split paths
    modified_locations = split_intersecting_paths(locations, dry_run=not args.apply)

    # Save if --apply
    if args.apply:
        with open(locations_file, 'w') as f:
            json.dump(modified_locations, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Changes saved to {locations_file}")
    elif not args.dry_run:
        print("\n⚠️  Use --apply to save changes or --dry-run to preview")
