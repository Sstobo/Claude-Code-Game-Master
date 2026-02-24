#!/usr/bin/env python3
"""
Extract dungeon locations from Dungeon Crawler Carl Book 1.
Focus on described spaces, rooms, bosses, levels, and dungeons.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

CHUNKS_DIR = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
OUTPUT_DIR = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
OUTPUT_FILE = OUTPUT_DIR / "locations.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Known locations and places from the book
KNOWN_LOCATIONS = {
    # Main dungeon structure
    "World Dungeon": {
        "type": "dungeon",
        "description": "The World Dungeon - a massive dungeon that has appeared over the world, causing a system-based apocalypse",
        "features": ["spawning point", "level structure", "boss chambers", "treasure rooms"]
    },

    # Floor/Level references (extract dynamically)

    # Specific named areas
    "The Hoarder's Room": {
        "type": "boss_chamber",
        "description": "Boss room of the Hoarder, a first floor boss",
        "features": ["treasure pile", "hoard", "boss spawn"]
    },
    "War Chieftain's Room": {
        "type": "boss_chamber",
        "description": "Boss chamber of a War Chieftain, identical in size to the Hoarder's room",
        "features": ["boss spawn"]
    },
    "Guild Hall": {
        "type": "safe_zone",
        "description": "A guild hall serving as a safe zone, likely a tutorial area",
        "features": ["guild functions", "training", "safety"]
    },
    "Tutorial Zone": {
        "type": "area",
        "description": "Tutorial area for new adventurers",
        "features": ["basic training", "safe spawn area"]
    },
    "Respawn Point": {
        "type": "dungeon_feature",
        "description": "Point where adventurers respawn after death",
        "features": ["revival", "resurrection"]
    },
    "Goblin Territory": {
        "type": "faction_area",
        "description": "Area inhabited and controlled by goblins",
        "features": ["goblin mobs", "goblin camps", "goblin artifacts"]
    },
    "Hobgoblin Territory": {
        "type": "faction_area",
        "description": "Area inhabited by more powerful hobgoblins",
        "features": ["hobgoblin mobs", "stronger enemies"]
    },
}

def extract_floor_references(content):
    """Extract floor/level references from content."""
    locations = {}

    # Find all floor/level mentions with context
    floor_patterns = [
        r'(?:floor|level|F|L)[\s:]?(\d+)',  # Floor N or Level N
        r'(\d+)(?:st|nd|rd|th)\s+(?:floor|level)',
        r'(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+(?:floor|level)',
    ]

    for pattern in floor_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                floor_num = match[0] if match[0] else match
            else:
                floor_num = match

            if floor_num.isdigit():
                loc_name = f"Floor {floor_num}"
            else:
                continue

            if loc_name not in locations:
                locations[loc_name] = {
                    "type": "floor",
                    "description": f"Dungeon Floor {floor_num}",
                    "features": []
                }

    return locations

def extract_room_descriptions(content):
    """Extract room and chamber descriptions."""
    locations = {}

    # Patterns for room descriptions
    room_patterns = [
        r'room[s]?(?:\s+(?:was|were|contained|had)|:)([^.!?]*[.!?])',
        r'chamber[s]?[^.]*?(?:was|were|contained|had)([^.!?]*[.!?])',
        r'(?:The room|This room|Here|The chamber)[^.]*?(?:was|were|had|contained)([^.!?]*[.!?])',
    ]

    for pattern in room_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for i, match in enumerate(matches):
            description = match.group(1).strip()
            if len(description) > 10:
                loc_name = f"Room Area {i}"
                locations[loc_name] = {
                    "type": "room",
                    "description": description[:200],  # Limit description length
                    "features": []
                }

    return locations

def extract_named_locations(content):
    """Extract named locations and landmarks."""
    locations = {}

    # Look for location names (capitalized, often with "the")
    named_loc_patterns = [
        r'(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:room|chamber|area|zone|level|floor|hall|vault|cavern|cave|tunnel|passage|pit|arena)',
        r'(?:left|right|went)\s+(?:towards|to|into|through)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]

    for pattern in named_loc_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            loc_name = match.strip()
            if len(loc_name) > 3 and loc_name not in locations and loc_name not in KNOWN_LOCATIONS:
                locations[loc_name] = {
                    "type": "area",
                    "description": f"Location: {loc_name}",
                    "features": []
                }

    return locations

def extract_dungeon_features(content):
    """Extract dungeon features and points of interest."""
    locations = {}

    features = re.findall(
        r'(?:found|discovered|encountered|saw|reached)\s+(?:a|an|the)\s+([^.!?]*?(?:door|gate|passage|corridor|tunnel|staircase|shaft|bridge|chasm|statue|trap|puzzle|chest|altar|throne|fountain|wall))[.!?]',
        content,
        re.IGNORECASE
    )

    for feature in features:
        feature = feature.strip()
        if 3 < len(feature) < 100:
            feature_name = feature.title()[:50]
            if feature_name not in locations:
                locations[feature_name] = {
                    "type": "feature",
                    "description": feature,
                    "features": []
                }

    return locations

def main():
    print("Extracting dungeon locations from Dungeon Crawler Carl Book 1...")
    print(f"Processing {len(list(CHUNKS_DIR.glob('chunk_*.txt')))} chunks...\n")

    all_locations = {}

    # Add known locations first
    all_locations.update(KNOWN_LOCATIONS)

    # Process all chunks
    chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))

    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Extract different types of locations
        floors = extract_floor_references(content)
        rooms = extract_room_descriptions(content)
        named_locs = extract_named_locations(content)
        features = extract_dungeon_features(content)

        # Merge (avoiding duplicates)
        for locs in [floors, rooms, named_locs, features]:
            for name, data in locs.items():
                if name not in all_locations:
                    all_locations[name] = data
                    if "name" not in all_locations[name]:
                        all_locations[name]["name"] = name

    # Finalize location objects with required fields
    for name, loc_data in all_locations.items():
        if "name" not in loc_data:
            loc_data["name"] = name
        if "connections" not in loc_data:
            loc_data["connections"] = []
        if "visited" not in loc_data:
            loc_data["visited"] = False

    # Create output structure
    output = {
        "metadata": {
            "source": "Dungeon Crawler Carl Book 1",
            "extraction_type": "Dungeon Locations and Areas",
            "extraction_date": "2026-02-23",
            "total_chunks_processed": len(chunk_files),
            "total_locations_found": len(all_locations)
        },
        "locations": all_locations
    }

    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Successfully extracted {len(all_locations)} locations")
    print(f"Wrote to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB\n")

    # Print summary
    print("Locations by type:")
    location_types = defaultdict(list)
    for loc_name, loc_data in all_locations.items():
        loc_type = loc_data.get("type", "unknown")
        location_types[loc_type].append(loc_name)

    for loc_type in sorted(location_types.keys()):
        print(f"  {loc_type}: {len(location_types[loc_type])}")

    print("\nSample locations:")
    for i, (name, data) in enumerate(list(all_locations.items())[:15]):
        print(f"  - {name} ({data.get('type', 'unknown')})")
        if "description" in data and data["description"]:
            desc = data["description"][:60].replace('\n', ' ')
            print(f"    > {desc}...")

if __name__ == "__main__":
    main()
