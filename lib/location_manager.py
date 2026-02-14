#!/usr/bin/env python3
"""
Location management module for DM tools
Handles location creation, connections, and descriptions
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
from path_manager import PathManager


class LocationManager(EntityManager):
    """Manage location operations. Inherits from EntityManager for common functionality."""

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.locations_file = "locations.json"
        self.path_manager = PathManager(str(self.campaign_dir))

    def add_location(self, name: str, position: str, from_location: str = None,
                    bearing: float = None, distance: float = None, terrain: str = "open") -> bool:
        """
        Add a new location with optional coordinate calculation

        Args:
            name: Location name
            position: Relative position description
            from_location: Origin location for coordinate calculation
            bearing: Direction in degrees (0=North)
            distance: Distance in meters
            terrain: Terrain type (open, forest, urban, etc.)

        Returns True on success, False on failure
        """
        # Validate name
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        # Check if location already exists
        if self._entity_exists(self.locations_file, name):
            print(f"[ERROR] Location '{name}' already exists")
            return False

        # Create location data
        location_data = {
            'position': position,
            'connections': [],
            'description': '',
            'discovered': self.get_timestamp(),
            'blocked_ranges': []
        }

        # Calculate coordinates if parameters provided
        if from_location and bearing is not None and distance:
            locations = self._load_entities(self.locations_file)

            if from_location not in locations:
                print(f"[ERROR] Origin location '{from_location}' not found")
                return False

            from_coords = locations[from_location].get('coordinates')
            if not from_coords:
                print(f"[ERROR] Origin location '{from_location}' has no coordinates")
                return False

            # Calculate destination coordinates
            from pathfinding import PathFinder
            pf = PathFinder()
            new_coords = pf.calculate_coordinates(from_coords, distance, bearing)
            location_data['coordinates'] = new_coords

            # Auto-create bidirectional connection
            reverse_bearing = pf.get_reverse_bearing(bearing)

            # Add connection from origin to new location
            if 'connections' not in locations[from_location]:
                locations[from_location]['connections'] = []

            locations[from_location]['connections'].append({
                'to': name,
                'path': f"{distance}m на {bearing}°",
                'distance_meters': int(distance),
                'bearing': bearing,
                'terrain': terrain
            })

            # Add reverse connection
            location_data['connections'].append({
                'to': from_location,
                'path': f"{distance}m на {reverse_bearing}°",
                'distance_meters': int(distance),
                'bearing': reverse_bearing,
                'terrain': terrain
            })

            # Save updated origin location
            self._save_entities(self.locations_file, locations)

            direction, abbr = pf.bearing_to_compass(bearing)
            print(f"[INFO] Calculated coordinates: {new_coords}")
            print(f"[INFO] Direction from {from_location}: {direction} ({abbr})")
            print(f"[INFO] Auto-created bidirectional connection")

        # Save new location
        if self._add_entity(self.locations_file, name, location_data):
            print(f"[SUCCESS] Added location: {name} ({position})")
            return True
        return False

    def connect_locations(self, from_loc: str, to_loc: str, path: str) -> bool:
        """
        Connect two locations bidirectionally
        """
        # Validate names
        for loc in [from_loc, to_loc]:
            valid, error = self.validators.validate_name(loc)
            if not valid:
                print(f"[ERROR] {error}")
                return False

        # Load locations
        locations = self._load_entities(self.locations_file)

        # Check both locations exist
        if from_loc not in locations:
            print(f"[ERROR] Location '{from_loc}' not found")
            return False
        if to_loc not in locations:
            print(f"[ERROR] Location '{to_loc}' not found")
            return False

        # Check if connection already exists
        existing_connections = [c['to'] for c in locations[from_loc].get('connections', [])]
        if to_loc in existing_connections:
            print(f"[ERROR] Connection already exists between '{from_loc}' and '{to_loc}'")
            return False

        # Add bidirectional connection
        if 'connections' not in locations[from_loc]:
            locations[from_loc]['connections'] = []
        if 'connections' not in locations[to_loc]:
            locations[to_loc]['connections'] = []

        locations[from_loc]['connections'].append({
            'to': to_loc,
            'path': path
        })
        locations[to_loc]['connections'].append({
            'to': from_loc,
            'path': path
        })

        if self._save_entities(self.locations_file, locations):
            print(f"[SUCCESS] Connected {from_loc} <-> {to_loc} via {path}")
            return True
        return False

    def set_description(self, name: str, description: str) -> bool:
        """
        Set or update location description
        """
        # Validate name
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        # Check if location exists
        if not self._entity_exists(self.locations_file, name):
            print(f"[ERROR] Location '{name}' not found")
            return False

        # Update description
        if self._update_entity(self.locations_file, name, {'description': description}):
            print(f"[SUCCESS] Updated description for {name}")
            return True
        return False

    def get_location(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get location data
        """
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return None

        location = self._get_entity(self.locations_file, name)
        if not location:
            print(f"[ERROR] Location '{name}' not found")
            return None

        return location

    def list_locations(self) -> List[str]:
        """
        List all location names
        """
        locations = self._load_entities(self.locations_file)
        return list(locations.keys())

    def get_connections(self, name: str) -> List[Dict[str, str]]:
        """
        Get connections for a location
        """
        location = self.get_location(name)
        if location:
            return location.get('connections', [])
        return []

    def decide_route(self, from_loc: str, to_loc: str) -> bool:
        """
        Interactive route decision - analyzes options and prompts DM to choose
        Returns True on success, False on failure
        """
        import json

        # Get navigation suggestion
        suggestion = self.path_manager.suggest_navigation(from_loc, to_loc)

        if suggestion.get("method") == "error":
            print(f"[ERROR] {suggestion.get('message')}")
            return False

        if suggestion.get("method") != "needs_decision":
            # Already decided
            cached = self.path_manager.get_cached_decision(from_loc, to_loc)
            if cached:
                print(f"[INFO] Decision already cached: {cached['decision']}")
                print(json.dumps(cached, indent=2, ensure_ascii=False))
                return True

        # Display options
        print("=" * 60)
        print(f"ROUTE DECISION: {from_loc} → {to_loc}")
        print("=" * 60)

        options = suggestion.get("options", {})
        analysis = suggestion.get("analysis", {})

        print("\nAVAILABLE OPTIONS:\n")

        option_keys = []

        if "direct" in options:
            opt = options["direct"]
            option_keys.append("direct")
            print(f"[1] DIRECT PATH")
            print(f"    Distance: {opt['distance']}m")
            print(f"    Direction: {opt['direction']}")
            print(f"    Bearing: {opt['bearing']}°")
            print()

        if "use_route" in options:
            opt = options["use_route"]
            option_keys.append("use_route")
            print(f"[2] USE EXISTING ROUTE")
            print(f"    Path: {' → '.join(opt['route'])}")
            print(f"    Distance: {opt['distance']}m")
            print(f"    Hops: {opt['hops']}")
            print()

        if "blocked_reason" in options:
            print(f"[!] DIRECT PATH BLOCKED: {options['blocked_reason']}\n")

        print(f"[3] BLOCK THIS ROUTE (permanently)")
        option_keys.append("blocked")
        print()

        print("=" * 60)
        print("Enter choice [1-3]: ", end='', flush=True)

        try:
            choice = input().strip()
            choice_num = int(choice)

            if choice_num < 1 or choice_num > len(option_keys) + 1:
                print(f"[ERROR] Invalid choice: {choice}")
                return False

            if choice_num == len(option_keys) + 1:
                # Block route
                print("Enter reason for blocking: ", end='', flush=True)
                reason = input().strip()
                self.path_manager.cache_decision(from_loc, to_loc, "blocked", reason=reason)
                print(f"[SUCCESS] Route blocked: {reason}")
                return True

            # Get selected decision
            decision = option_keys[choice_num - 1]

            if decision == "direct":
                self.path_manager.cache_decision(from_loc, to_loc, "direct")
                print(f"[SUCCESS] Cached decision: use direct path")

            elif decision == "use_route":
                route = options["use_route"]["route"]
                self.path_manager.cache_decision(from_loc, to_loc, "use_route", route=route)
                print(f"[SUCCESS] Cached decision: use route through {len(route)-2} locations")

            return True

        except (ValueError, KeyboardInterrupt, EOFError):
            print("\n[ERROR] Invalid input or cancelled")
            return False

    def show_routes(self, from_loc: str, to_loc: str) -> bool:
        """
        Show all possible routes between two locations
        Returns True on success, False on failure
        """
        import json

        analysis = self.path_manager.analyze_route_options(from_loc, to_loc)

        if analysis.get("error"):
            print(f"[ERROR] {analysis['error']}")
            return False

        print("=" * 60)
        print(f"ROUTES: {from_loc} → {to_loc}")
        print("=" * 60)
        print()

        # Check cached decision
        cached = self.path_manager.get_cached_decision(from_loc, to_loc)
        if cached:
            print(f"CACHED DECISION: {cached['decision']}")
            if cached.get('reason'):
                print(f"  Reason: {cached['reason']}")
            if cached.get('route'):
                print(f"  Route: {' → '.join(cached['route'])}")
            print()

        # Direct path
        if analysis.get("direct_distance"):
            print(f"DIRECT PATH:")
            print(f"  Distance: {analysis['direct_distance']}m")
            print(f"  Bearing: {analysis['direct_bearing']}°")

            from pathfinding import PathFinder
            pf = PathFinder()
            direction, abbr = pf.bearing_to_compass(analysis['direct_bearing'])
            print(f"  Direction: {direction} ({abbr})")

            if analysis.get("direct_blocked"):
                print(f"  ⚠ BLOCKED: {analysis['blocked_reason']}")
            print()

        # Existing routes
        existing_routes = analysis.get("existing_routes", [])
        if existing_routes:
            print(f"EXISTING ROUTES ({len(existing_routes)}):")
            for i, route in enumerate(existing_routes, 1):
                print(f"\n  Route {i}:")
                print(f"    Path: {' → '.join(route['path'])}")
                print(f"    Distance: {route['distance']}m")
                print(f"    Hops: {route['hops']}")
        else:
            print("NO EXISTING ROUTES FOUND")

        print()
        print("=" * 60)
        return True

    def block_direction(self, location: str, from_deg: float, to_deg: float, reason: str) -> bool:
        """
        Add blocked direction range to a location
        Returns True on success, False on failure
        """
        # Load locations
        locations = self._load_entities(self.locations_file)

        if location not in locations:
            print(f"[ERROR] Location '{location}' not found")
            return False

        # Initialize blocked_ranges if needed
        if 'blocked_ranges' not in locations[location]:
            locations[location]['blocked_ranges'] = []

        # Check for overlaps
        for block in locations[location]['blocked_ranges']:
            if (from_deg <= block['to'] and to_deg >= block['from']):
                print(f"[WARNING] Range overlaps with existing block: {block['from']}° - {block['to']}°")

        # Add new block
        locations[location]['blocked_ranges'].append({
            'from': from_deg,
            'to': to_deg,
            'reason': reason
        })

        if self._save_entities(self.locations_file, locations):
            print(f"[SUCCESS] Blocked {from_deg}° - {to_deg}° at {location}: {reason}")
            return True
        return False

    def unblock_direction(self, location: str, from_deg: float, to_deg: float) -> bool:
        """
        Remove blocked direction range from a location
        Returns True on success, False on failure
        """
        # Load locations
        locations = self._load_entities(self.locations_file)

        if location not in locations:
            print(f"[ERROR] Location '{location}' not found")
            return False

        if 'blocked_ranges' not in locations[location]:
            print(f"[ERROR] No blocked ranges at {location}")
            return False

        # Find and remove matching block
        original_count = len(locations[location]['blocked_ranges'])
        locations[location]['blocked_ranges'] = [
            block for block in locations[location]['blocked_ranges']
            if not (block['from'] == from_deg and block['to'] == to_deg)
        ]

        new_count = len(locations[location]['blocked_ranges'])
        if new_count == original_count:
            print(f"[ERROR] No matching blocked range found: {from_deg}° - {to_deg}°")
            return False

        if self._save_entities(self.locations_file, locations):
            print(f"[SUCCESS] Unblocked {from_deg}° - {to_deg}° at {location}")
            return True
        return False

    def create_batch(self, locations_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple locations in batch

        Args:
            locations_data: List of location dictionaries with name, description, position, etc.

        Returns:
            List of results for each location with success/error status
        """
        results = []
        locations = self._load_entities(self.locations_file)

        for loc_data in locations_data:
            result = {'name': loc_data.get('name', 'Unknown')}

            # Validate required fields
            if not loc_data.get('name'):
                result['success'] = False
                result['error'] = 'Missing location name'
                results.append(result)
                continue

            name = loc_data['name']

            # Check for duplicates
            if name in locations:
                result['success'] = False
                result['error'] = f'Location {name} already exists'
                results.append(result)
                continue

            # Create location entry
            location_entry = {
                'position': loc_data.get('position', 'unknown'),
                'description': loc_data.get('description', ''),
                'connections': [],
                'discovered': self.get_timestamp()
            }

            # Add source if provided
            if loc_data.get('source'):
                location_entry['source'] = loc_data['source']

            # Process connections if provided
            if loc_data.get('connections'):
                for conn_name in loc_data['connections']:
                    location_entry['connections'].append({
                        'to': conn_name,
                        'path': 'connected'
                    })

            # Add notes if provided
            if loc_data.get('notes'):
                location_entry['notes'] = loc_data['notes']

            # Add to locations dictionary (pending save)
            locations[name] = location_entry
            result['_pending'] = True
            results.append(result)

        # Save all locations at once, then mark success/failure
        pending = [r for r in results if r.get('_pending')]
        if pending:
            saved = self._save_entities(self.locations_file, locations)
            for result in pending:
                del result['_pending']
                if saved:
                    result['success'] = True
                else:
                    result['success'] = False
                    result['error'] = 'Failed to save to file'

        return results


def main():
    """CLI interface for location management"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Location management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Add location
    add_parser = subparsers.add_parser('add', help='Add new location')
    add_parser.add_argument('name', help='Location name')
    add_parser.add_argument('position', help='Relative position')
    add_parser.add_argument('--from', dest='from_location', help='Origin location for coordinates')
    add_parser.add_argument('--bearing', type=float, help='Direction in degrees (0=North)')
    add_parser.add_argument('--distance', type=float, help='Distance in meters')
    add_parser.add_argument('--terrain', default='open', help='Terrain type (open, forest, urban, etc.)')

    # Connect locations
    connect_parser = subparsers.add_parser('connect', help='Connect two locations')
    connect_parser.add_argument('from_loc', help='From location')
    connect_parser.add_argument('to_loc', help='To location')
    connect_parser.add_argument('path', help='Path description')

    # Describe location
    describe_parser = subparsers.add_parser('describe', help='Set location description')
    describe_parser.add_argument('name', help='Location name')
    describe_parser.add_argument('description', help='Description text')

    # Get location
    get_parser = subparsers.add_parser('get', help='Get location info')
    get_parser.add_argument('name', help='Location name')

    # List locations
    subparsers.add_parser('list', help='List all locations')

    # Get connections
    connections_parser = subparsers.add_parser('connections', help='Get location connections')
    connections_parser.add_argument('name', help='Location name')

    # Decide route
    decide_parser = subparsers.add_parser('decide', help='Decide route between locations')
    decide_parser.add_argument('from_loc', help='From location')
    decide_parser.add_argument('to_loc', help='To location')

    # Show routes
    routes_parser = subparsers.add_parser('routes', help='Show all possible routes')
    routes_parser.add_argument('from_loc', help='From location')
    routes_parser.add_argument('to_loc', help='To location')

    # Block direction
    block_parser = subparsers.add_parser('block', help='Block direction range')
    block_parser.add_argument('location', help='Location name')
    block_parser.add_argument('from_deg', type=float, help='From bearing (degrees)')
    block_parser.add_argument('to_deg', type=float, help='To bearing (degrees)')
    block_parser.add_argument('reason', help='Reason for blocking')

    # Unblock direction
    unblock_parser = subparsers.add_parser('unblock', help='Unblock direction range')
    unblock_parser.add_argument('location', help='Location name')
    unblock_parser.add_argument('from_deg', type=float, help='From bearing (degrees)')
    unblock_parser.add_argument('to_deg', type=float, help='To bearing (degrees)')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = LocationManager()

    if args.action == 'add':
        if not manager.add_location(
            args.name,
            args.position,
            from_location=args.from_location,
            bearing=args.bearing,
            distance=args.distance,
            terrain=args.terrain
        ):
            sys.exit(1)

    elif args.action == 'connect':
        if not manager.connect_locations(args.from_loc, args.to_loc, args.path):
            sys.exit(1)

    elif args.action == 'describe':
        if not manager.set_description(args.name, args.description):
            sys.exit(1)

    elif args.action == 'get':
        location = manager.get_location(args.name)
        if location:
            print(json.dumps({args.name: location}, indent=2))
        else:
            sys.exit(1)

    elif args.action == 'list':
        locations = manager.list_locations()
        if locations:
            for loc in locations:
                print(f"  - {loc}")
        else:
            print("No locations found")

    elif args.action == 'connections':
        connections = manager.get_connections(args.name)
        if connections:
            print(json.dumps(connections, indent=2))
        else:
            print("No connections found")

    elif args.action == 'decide':
        if not manager.decide_route(args.from_loc, args.to_loc):
            sys.exit(1)

    elif args.action == 'routes':
        if not manager.show_routes(args.from_loc, args.to_loc):
            sys.exit(1)

    elif args.action == 'block':
        if not manager.block_direction(args.location, args.from_deg, args.to_deg, args.reason):
            sys.exit(1)

    elif args.action == 'unblock':
        if not manager.unblock_direction(args.location, args.from_deg, args.to_deg):
            sys.exit(1)


if __name__ == "__main__":
    main()
