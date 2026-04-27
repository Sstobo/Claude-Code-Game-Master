#!/usr/bin/env python3
"""
Clean extraction of Dungeon Crawler Carl locations.
Removes generic room descriptions and focuses on meaningful locations.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

CHUNKS_DIR = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
OUTPUT_DIR = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
OUTPUT_FILE = OUTPUT_DIR / "locations.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class CleanLocationExtractor:
    def __init__(self):
        self.locations = {}
        self.mention_count = defaultdict(int)

    def is_valid_location_name(self, name):
        """Filter out generic/noise names."""
        name = name.strip()

        # Skip very short names
        if len(name) < 3:
            return False

        # Skip names that are obviously not locations
        noise_patterns = [
            r'^(back|front|side|bottom|top|center|middle|end|start|left|right|wall|floor|ceiling|corner|area|room|of|the|and|or|a|an|in|on|at|to|from)$',
            r'^(cart|door|box|container|pile|stack|wall|hallway)$',
            r'^(steps?|stairs?|passage|corridor)$',
            r'^\w+ing out',  # Gerunds like "stepping out"
            r'^\w+ting\s+\w+',  # Participles
        ]

        lower_name = name.lower()
        for pattern in noise_patterns:
            if re.match(pattern, lower_name):
                return False

        # Skip names that are too generic
        if len(name.split()) > 5:
            return False

        # Must have at least one capital letter (proper noun)
        if not any(c.isupper() for c in name):
            return False

        # Skip common non-location words
        if name in ["His", "Her", "The", "This", "That", "What", "Where", "Why"]:
            return False

        return True

    def add_location(self, name, loc_type, description=""):
        """Add a validated location."""
        if self.is_valid_location_name(name):
            if name not in self.locations:
                self.locations[name] = {
                    "name": name,
                    "type": loc_type,
                    "description": description,
                    "connections": [],
                    "features": [],
                    "visited": False,
                    "discovered": False
                }
            self.mention_count[name] += 1

    def add_floor(self, floor_num, name=None):
        """Add a dungeon floor."""
        if isinstance(floor_num, str):
            if not floor_num.isdigit():
                # Convert ordinal to number
                ordinals = {
                    "first": "1", "second": "2", "third": "3",
                    "fourth": "4", "fifth": "5", "sixth": "6",
                    "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10",
                }
                floor_num = ordinals.get(floor_num.lower(), floor_num)

        floor_name = name if name else f"Floor {floor_num}"
        self.add_location(
            floor_name,
            "dungeon_floor",
            f"Dungeon Floor {floor_num}"
        )

    def extract_from_chunk(self, content):
        """Extract locations from chunk content."""

        # Pattern 1: Floor/Level numbers
        floor_refs = re.findall(
            r'(?:floor|level)\s+(\d+|[Ff]irst|[Ss]econd|[Tt]hird)',
            content,
            re.IGNORECASE
        )
        for floor_ref in floor_refs:
            self.add_floor(floor_ref)

        # Pattern 2: Specific named areas
        if re.search(r'\bTutorial Guild Hall\b', content):
            self.add_location(
                "Tutorial Guild Hall",
                "safe_zone",
                "Tutorial Guild Hall - A safe zone for new adventurers"
            )

        if re.search(r'\bGuild Hall\b', content) and "Tutorial" not in content:
            self.add_location(
                "Guild Hall",
                "safe_zone",
                "Guild Hall - A safe zone for adventurers"
            )

        # Pattern 3: Dungeon name references
        if re.search(r'\bWorld Dungeon\b', content):
            self.add_location(
                "World Dungeon",
                "dungeon",
                "The World Dungeon - massive 18-level dungeon that appeared worldwide"
            )

        if re.search(r'\bDungeon Floor 1\b', content):
            self.add_location(
                "Dungeon Floor 1",
                "dungeon_zone",
                "First Floor of the World Dungeon"
            )

        # Pattern 4: Boss chambers
        if re.search(r'\b[Hh]oarder\b', content):
            self.add_location(
                "Hoarder's Chamber",
                "boss_chamber",
                "Boss chamber of the Hoarder - contains massive treasure hoard"
            )

        if re.search(r'\b[Ww]ar\s+[Cc]hieftain\b', content):
            self.add_location(
                "War Chieftain's Chamber",
                "boss_chamber",
                "Boss chamber of the War Chieftain"
            )

        # Pattern 5: Entrance locations
        if re.search(r'dungeon.*entrance|entrance.*dungeon', content, re.IGNORECASE):
            self.add_location(
                "Dungeon Entrance",
                "entrance",
                "Main entrance to the World Dungeon"
            )

        # Pattern 6: Faction territories
        if re.search(r'\bgoblin\b', content, re.IGNORECASE):
            self.add_location(
                "Goblin Territory",
                "faction_area",
                "Areas inhabited and controlled by goblins"
            )

        if re.search(r'\bhobgoblin\b', content, re.IGNORECASE):
            self.add_location(
                "Hobgoblin Territory",
                "faction_area",
                "Areas controlled by stronger hobgoblins"
            )

        # Pattern 7: Special features
        if re.search(r'\bmarble\b.*\b(?:floor|chamber)', content, re.IGNORECASE):
            self.add_location(
                "Marble Chamber",
                "special_feature",
                "Chamber with marble flooring"
            )

        if re.search(r'(?:thirty|30)\s+feet\s+tall.*door|grand.*door', content, re.IGNORECASE):
            self.add_location(
                "Grand Entrance Door",
                "feature",
                "Large thirty-foot tall door marking dungeon entrance"
            )

        # Pattern 8: Hazard zones
        if re.search(r'level.*collapse|reclaim|time.*limit', content, re.IGNORECASE):
            self.add_location(
                "Level Collapse Zone",
                "hazard_area",
                "Areas subject to level reclamation and collapse"
            )

        # Pattern 9: Respawn areas
        if re.search(r'respawn|resurrect|revival', content, re.IGNORECASE):
            self.add_location(
                "Respawn Point",
                "safe_zone",
                "Location where adventurers respawn after death"
            )

    def extract_all(self):
        """Extract from all chunks."""
        chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))

        for i, chunk_file in enumerate(chunk_files):
            if (i + 1) % 100 == 0:
                print(f"Processing chunk {i + 1}/{len(chunk_files)}...")

            with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            self.extract_from_chunk(content)

    def get_output(self):
        """Generate JSON output."""
        by_type = defaultdict(list)
        for loc_name, loc_data in self.locations.items():
            loc_type = loc_data.get("type", "unknown")
            by_type[loc_type].append(loc_name)

        return {
            "metadata": {
                "source": "Dungeon Crawler Carl Book 1",
                "extraction_type": "Dungeon Locations and Areas",
                "extraction_date": "2026-02-23",
                "total_chunks_processed": 332,
                "total_unique_locations": len(self.locations)
            },
            "locations": self.locations,
            "location_types": {
                loc_type: [
                    {
                        "name": loc_name,
                        "mentions": self.mention_count[loc_name]
                    }
                    for loc_name in sorted(locations)
                ]
                for loc_type, locations in by_type.items()
            }
        }

def main():
    print("=" * 70)
    print("DUNGEON CRAWLER CARL - CLEAN LOCATION EXTRACTION")
    print("=" * 70)
    print()

    extractor = CleanLocationExtractor()
    extractor.extract_all()

    output = extractor.get_output()

    # Write JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("EXTRACTION COMPLETE")
    print(f"  Total locations: {len(extractor.locations)}")
    print(f"  Output file: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print()

    print("LOCATIONS BY TYPE:")
    print("-" * 70)
    for loc_type in sorted(output["location_types"].keys()):
        count = len(output["location_types"][loc_type])
        print(f"  {loc_type:25} : {count:3} locations")

    print()
    print("ALL LOCATIONS:")
    print("-" * 70)
    for loc_type in sorted(output["location_types"].keys()):
        print(f"\n{loc_type.upper()}:")
        for item in output["location_types"][loc_type]:
            loc = item["name"]
            desc = extractor.locations[loc]["description"]
            print(f"  • {loc}")
            if desc:
                print(f"    {desc}")

    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
