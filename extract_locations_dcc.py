#!/usr/bin/env python3
"""Extract locations from Dungeon Crawler Carl chunks."""

import json
import re
from pathlib import Path
from collections import defaultdict

def extract_locations_from_chunks():
    """Read all chunks and extract location information."""

    chunks_dir = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
    locations = {}
    seen_locations = set()

    # Process each chunk
    chunk_files = sorted(chunks_dir.glob("chunk_*.txt"))
    print(f"Processing {len(chunk_files)} chunk files...")

    all_text = ""

    for chunk_file in chunk_files:
        try:
            # Try different encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(chunk_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        break
                except (UnicodeDecodeError, OSError):
                    continue

            if content is None:
                print(f"Could not decode {chunk_file}")
                continue

            all_text += "\n" + content

        except Exception as e:
            print(f"Error processing {chunk_file}: {e}")

    # Extract locations from combined text

    # Known locations with floor and description patterns
    known_locations = {
        "Third Floor - Golden Hallway": {
            "description": "A long, golden hallway with golden-colored bricks and a plush red carpet. The ceiling features an illusory dark sky with stars and nebula. Located just beyond the green room transition.",
            "floor": 3,
            "type": "transition",
            "connections": ["Mordecai's Guild Hall"],
            "notes": ["Illusory outdoor sky ceiling", "Red carpet path"]
        },
        "Mordecai's Guild Hall": {
            "description": "A guild hall run by Mordecai on Floor 3. Contains training and examination facilities, including beds for transformations and character development screens. Functions as the entry point to the third floor proper.",
            "floor": 3,
            "type": "safe_zone",
            "connections": ["Third Floor - Golden Hallway", "Training Room"],
            "notes": ["Guildmaster: Mordecai (Level 50 Incubus)", "Character transformation beds available", "Safe from combat"]
        },
        "Training Room": {
            "description": "A room within Mordecai's Guild Hall where adventurers can undergo character modifications, race selection, and class choices. Features floating screens for menu interaction.",
            "floor": 3,
            "type": "facility",
            "connections": ["Mordecai's Guild Hall"],
            "notes": ["Character development area", "Examination conducted here"]
        }
    }

    # Find floor references
    floor_pattern = r'(?:Welcome|to|the)\s+(?:Third|3rd)\s+Floor'
    if re.search(floor_pattern, all_text, re.IGNORECASE):
        floor_3 = "Third Floor"
        if floor_3 not in seen_locations:
            locations[floor_3] = {
                "description": "The third level of the World Dungeon. The training levels have concluded and 'the games may truly begin.' Features advanced challenges and urban-themed areas.",
                "floor": 3,
                "type": "floor",
                "connections": ["Mordecai's Guild Hall", "Third Floor - Golden Hallway"],
                "notes": ["Previous level collapses in 3+ hours", "End of training levels", "Beginning of actual dungeon progression"]
            }
            seen_locations.add(floor_3)

    # Find additional floors
    for match in re.finditer(r'(?:Floor|Level)\s+(\d+)', all_text, re.IGNORECASE):
        floor_num = match.group(1)
        floor_name = f"Floor {floor_num}"

        if floor_name not in seen_locations:
            locations[floor_name] = {
                "description": f"Floor {floor_num} of the World Dungeon",
                "floor": floor_num,
                "type": "floor",
                "connections": [],
                "notes": []
            }
            seen_locations.add(floor_name)

    # Find specific area patterns in context
    area_patterns = [
        (r'(?:green\s+room)', "Green Room", "transition_room", 1),
        (r"(?:[Oo]dette's\s+stage)", "Odette's Stage", "performance_area", 2),
        (r'(?:sixth\s+floor)', "Sixth Floor", "floor", 6),
        (r'(?:urban\s+levels?)', "Urban Levels", "region", None),
        (r'(?:Over\s+City)', "Over City", "region", None),
    ]

    for pattern, name, area_type, floor in area_patterns:
        if re.search(pattern, all_text, re.IGNORECASE) and name not in seen_locations:
            locations[name] = {
                "description": f"An area in the dungeon",
                "type": area_type,
                "connections": [],
                "notes": []
            }
            if floor:
                locations[name]["floor"] = floor
            seen_locations.add(name)

    # Add known locations
    locations.update(known_locations)

    return locations

def main():
    """Main execution."""
    print("Extracting locations from Dungeon Crawler Carl chunks...")

    locations = extract_locations_from_chunks()

    # Add more locations from known story content
    additional_locations = {
        "The Over City - Floor 3": {
            "description": "A sprawling urban area on Floor 3 with hundreds of scattered villages surrounded by wide swaths of abandoned city. Features medieval-style architecture and diverse NPCs including dwarves, humans, orcs, and elf-like creatures.",
            "floor": 3,
            "type": "city",
            "connections": ["Floor 3", "Floor 6"],
            "notes": [
                "Over City levels appear every 3 floors",
                "Random entry/exit points",
                "Contains multiple villages and abandoned city sections",
                "Wooden streets",
                "Multiple NPC faction areas"
            ]
        },
        "The Over City - Floor 6": {
            "description": "The second Over City level in the dungeon, appearing as part of the tradition. Contains urban environments mixed with various themes.",
            "floor": 6,
            "type": "city",
            "connections": ["Floor 6"],
            "notes": ["Urban levels appear every 3 floors"]
        }
    }

    locations.update(additional_locations)

    # Convert to the expected format
    output = {}
    for loc_name, loc_data in locations.items():
        loc_output = {
            "description": loc_data.get("description", "A location in the dungeon"),
            "type": loc_data.get("type", "area"),
            "connections": loc_data.get("connections", []),
            "notes": loc_data.get("notes", [])
        }
        if "floor" in loc_data:
            loc_output["floor"] = loc_data["floor"]
        output[loc_name] = loc_output

    # Write output
    output_file = Path("world-state/campaigns/dungeon-crawler-carl/extracted/locations.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(output)} locations")
    print(f"Output written to: {output_file}")

    # Print summary
    print("\nLocation types:")
    type_counts = defaultdict(int)
    for loc in output.values():
        type_counts[loc.get("type", "unknown")] += 1

    for loc_type, count in sorted(type_counts.items()):
        print(f"  {loc_type}: {count}")

    print("\nKey locations by floor:")
    by_floor = defaultdict(list)
    for loc_name, loc_data in output.items():
        if "floor" in loc_data:
            by_floor[loc_data["floor"]].append(loc_name)

    for floor in sorted(by_floor.keys(), key=lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 999):
        print(f"  Floor {floor}: {', '.join(sorted(by_floor[floor]))}")

if __name__ == "__main__":
    main()
