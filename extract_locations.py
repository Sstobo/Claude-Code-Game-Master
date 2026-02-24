#!/usr/bin/env python3
"""
Extract all locations from Dungeon Crawler Carl Book 1 chunks.
Reads all chunk files and creates a comprehensive locations.json.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Configuration
CHUNKS_DIR = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
OUTPUT_DIR = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
OUTPUT_FILE = OUTPUT_DIR / "locations.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Common location patterns and keywords
LOCATION_PATTERNS = {
    "dungeon": r"(?:Dungeon|dungeon|Chamber|chamber|Room|room|Hall|hall|Corridor|corridor|Cavern|cavern|Tunnel|tunnel|Cave|cave|Vault|vault)",
    "floor": r"(?:\d+(?:st|nd|rd|th)\s+(?:Floor|floor|Level|level))",
    "area": r"(?:Area|area|District|district|Zone|zone|Sector|sector)",
    "structure": r"(?:Tower|tower|Castle|castle|Temple|temple|Shrine|shrine|Keep|keep|Fort|fort|Palace|palace|Building|building|House|house)",
    "outdoor": r"(?:Forest|forest|Mountain|mountain|Valley|valley|Plain|plain|Desert|desert|Swamp|swamp|River|river|Lake|lake|Sea|sea|Ocean|ocean|Ruins|ruins)",
    "settlement": r"(?:Town|town|City|city|Village|village|Hamlet|hamlet|Camp|camp)",
}

def extract_locations_from_chunks():
    """Extract all locations from all chunk files."""
    locations = {}
    location_mentions = defaultdict(list)

    # Get all chunk files
    chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))
    print(f"Found {len(chunk_files)} chunk files")

    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Extract location names (capitalized phrases that look like place names)
        # Pattern: Capitalized words that appear to be location names
        location_names = re.findall(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Dungeon|Floor|Room|Chamber|Tower|Temple|Hall|Zone|District|Area|Level|Cavern|Cave|Tunnel|Keep|Valley|Ruins|Camp))?)\b',
            content
        )

        for location in location_names:
            if location not in location_mentions:
                location_mentions[location] = []
            location_mentions[location].append(chunk_file.name)

    # Filter and categorize locations
    # Remove common non-location words
    common_words = {
        'The', 'A', 'An', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'From',
        'Is', 'Was', 'Were', 'Are', 'Be', 'Been', 'Being', 'Have', 'Has', 'Had',
        'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should', 'May', 'Might',
        'Must', 'Shall', 'Can', 'Carl', 'Dungeon', 'Crawler', 'Book', 'Chapter',
        'He', 'She', 'It', 'They', 'Their', 'What', 'Which', 'Who', 'How', 'Why',
        'When', 'Where', 'There', 'Here', 'This', 'That', 'These', 'Those', 'I',
    }

    # Create location objects for valid locations
    for location_name, chunks in sorted(location_mentions.items()):
        # Skip if too common or too generic
        if location_name in common_words or len(location_name) < 3:
            continue

        # Skip single-word generic terms unless they're clearly locations
        if len(location_name.split()) == 1 and location_name not in ['Dungeon', 'Floor', 'Chamber', 'Tower', 'Temple', 'Castle', 'Vale', 'Forest', 'Mountain']:
            continue

        locations[location_name] = {
            "name": location_name,
            "description": f"Location mentioned in Dungeon Crawler Carl Book 1",
            "connections": [],
            "areas": [],
            "features": [],
            "visited": False,
            "discovered": len(chunks) > 1,
            "chunks_found": chunks,
            "mention_count": len(chunks)
        }

    return locations

def analyze_dungeon_structure():
    """Analyze dungeon structure and connections from chunks."""
    structure = {
        "levels": {},
        "rooms": {},
        "connections": []
    }

    chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))

    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Extract floor/level references
        floors = re.findall(r'(\d+)(?:st|nd|rd|th)\s+(?:Floor|floor|Level|level)', content)
        for floor in floors:
            if floor not in structure["levels"]:
                structure["levels"][floor] = {
                    "level": floor,
                    "rooms": [],
                    "features": []
                }

        # Extract room references
        rooms = re.findall(r'(?:Room|room|Chamber|chamber|Corridor|corridor|Hall|hall)\s+#?(\w+|\d+)', content)
        for room in rooms:
            if room not in structure["rooms"]:
                structure["rooms"][room] = {
                    "name": room,
                    "description": "",
                    "connections": []
                }

    return structure

def main():
    print("Extracting locations from Dungeon Crawler Carl Book 1 chunks...")

    # Extract locations
    locations = extract_locations_from_chunks()
    print(f"Found {len(locations)} unique locations")

    # Analyze dungeon structure
    structure = analyze_dungeon_structure()

    # Create output structure
    output = {
        "metadata": {
            "source": "Dungeon Crawler Carl Book 1",
            "extraction_date": "2026-02-23",
            "total_chunks_processed": 332,
            "total_locations_found": len(locations)
        },
        "dungeon_structure": structure,
        "locations": locations
    }

    # Write to JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Successfully wrote {len(locations)} locations to {OUTPUT_FILE}")
    print(f"Output file size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    # Print summary
    print("\nTop 20 most-mentioned locations:")
    sorted_locations = sorted(
        locations.items(),
        key=lambda x: x[1]['mention_count'],
        reverse=True
    )[:20]

    for name, data in sorted_locations:
        print(f"  - {name}: {data['mention_count']} mentions")

if __name__ == "__main__":
    main()
