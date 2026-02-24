#!/usr/bin/env python3
"""
Refined extraction: Focus on dungeon locations, rooms, areas, and geographic places.
Filters out character names and items.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

CHUNKS_DIR = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
OUTPUT_DIR = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
OUTPUT_FILE = OUTPUT_DIR / "locations.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_locations_from_chunks():
    """Extract dungeon locations and geographic areas."""
    locations = {}

    chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))

    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Extract explicit location/dungeon references
        # Pattern 1: "Floor X" or "Level X"
        floors = re.findall(r'([FfLl]loor|[Ll]evel)\s+(\d+)', content)
        for match in floors:
            floor_type, floor_num = match
            location_name = f"{floor_type.capitalize()} {floor_num}"
            if location_name not in locations:
                locations[location_name] = {
                    "name": location_name,
                    "type": "floor",
                    "description": f"{floor_type.capitalize()} {floor_num} of the dungeon",
                    "connections": [],
                    "features": [],
                    "visited": False
                }

        # Pattern 2: Explicit "Room X" references
        rooms = re.findall(r'(?:Room|Chamber)\s+(\d+|[A-Z][a-z]+)', content)
        for room in rooms:
            location_name = f"Room {room}"
            if location_name not in locations:
                locations[location_name] = {
                    "name": location_name,
                    "type": "room",
                    "description": f"Room {room} in the dungeon",
                    "connections": [],
                    "features": [],
                    "visited": False
                }

        # Pattern 3: Named dungeon areas (all caps or specific patterns)
        dungeon_areas = re.findall(
            r'\b(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Chamber|Hall|Vault|Cavern|Tunnel|Passage|Pit|Pit|Arena|Shrine|Sanctuary)))\b',
            content
        )
        for area in dungeon_areas:
            if area not in locations:
                locations[area] = {
                    "name": area,
                    "type": "area",
                    "description": f"Dungeon area: {area}",
                    "connections": [],
                    "features": [],
                    "visited": False
                }

        # Pattern 4: Geographic/dungeon descriptors
        features = re.findall(
            r'(?:through|in|at|near)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Passage|Gate|Door|Entrance|Exit|Shaft|Staircase|Bridge|Chasm|Pit))',
            content
        )
        for feature in features:
            if feature not in locations:
                locations[feature] = {
                    "name": feature,
                    "type": "feature",
                    "description": f"Dungeon feature: {feature}",
                    "connections": [],
                    "features": [],
                    "visited": False
                }

        # Pattern 5: "The X" style locations (likely dungeon areas)
        the_locations = re.findall(
            r'(?:enter|exit|leave|find|discover)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:Dungeon|Cavern|Crypt|Vault|Core|Throne|Library|Treasury|Armory|Kitchen|Barracks)?)\b',
            content
        )
        for loc in the_locations:
            if loc and len(loc) > 3 and loc not in locations:
                locations[loc] = {
                    "name": loc,
                    "type": "dungeon_area",
                    "description": f"Dungeon location: {loc}",
                    "connections": [],
                    "features": [],
                    "visited": False
                }

    return locations

def analyze_dungeon_layout():
    """Analyze connections between dungeon areas."""
    connections = defaultdict(list)
    chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))

    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Look for connection patterns: "from X to Y", "between X and Y", "X leads to Y"
        connection_patterns = [
            r'(?:from|via|through)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:to|into)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:leads|opens|connects|goes)\s+(?:to|into)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]

        for pattern in connection_patterns:
            matches = re.findall(pattern, content)
            for source, dest in matches:
                connections[source].append(dest)
                connections[dest].append(source)

    return connections

def main():
    print("Refining location extraction from Dungeon Crawler Carl Book 1...")

    # Extract locations
    locations = extract_locations_from_chunks()
    print(f"Extracted {len(locations)} dungeon locations/areas")

    # Analyze connections
    connections = analyze_dungeon_layout()

    # Add connection data to locations
    for loc_name, location in locations.items():
        if loc_name in connections:
            location["connections"] = list(set(connections[loc_name]))

    # Create comprehensive output
    output = {
        "metadata": {
            "source": "Dungeon Crawler Carl Book 1",
            "extraction_type": "Dungeon Locations and Areas",
            "extraction_date": "2026-02-23",
            "total_locations_found": len(locations)
        },
        "locations": locations,
        "location_types": {
            "floor": [loc for loc in locations.values() if loc.get("type") == "floor"],
            "room": [loc for loc in locations.values() if loc.get("type") == "room"],
            "area": [loc for loc in locations.values() if loc.get("type") == "area"],
            "feature": [loc for loc in locations.values() if loc.get("type") == "feature"],
            "dungeon_area": [loc for loc in locations.values() if loc.get("type") == "dungeon_area"],
        }
    }

    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote locations to {OUTPUT_FILE}")

    # Print summary
    print("\nLocation breakdown by type:")
    for loc_type, locs in output["location_types"].items():
        print(f"  {loc_type}: {len(locs)}")

    print("\nSample locations by type:")
    for loc_type in ["floor", "room", "area", "feature", "dungeon_area"]:
        samples = output["location_types"][loc_type][:3]
        if samples:
            print(f"\n  {loc_type.upper()}:")
            for sample in samples:
                print(f"    - {sample['name']}")

if __name__ == "__main__":
    main()
