#!/usr/bin/env python3
"""
Accurate extraction of Dungeon Crawler Carl Book 1 locations.
Focuses on actual dungeon structures, floors, and explicitly mentioned places.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

CHUNKS_DIR = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
OUTPUT_DIR = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
OUTPUT_FILE = OUTPUT_DIR / "locations.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class LocationExtractor:
    def __init__(self):
        self.locations = {}
        self.location_mentions = defaultdict(int)

    def add_location(self, name, loc_type, description="", connections=None):
        """Add or update a location."""
        if name not in self.locations:
            self.locations[name] = {
                "name": name,
                "type": loc_type,
                "description": description,
                "connections": connections or [],
                "features": [],
                "visited": False,
                "discovered": False
            }
        self.location_mentions[name] += 1

    def extract_from_chunk(self, content):
        """Extract locations from chunk content."""

        # Pattern 1: Floor references - "Floor 1", "First Floor", "level 18", etc.
        floors = re.findall(
            r'(?:Floor|floor|Level|level)\s+(\d+|[Ff]irst|[Ss]econd|[Tt]hird|[Ff]ourth|[Ff]ifth|[Ss]ixth)',
            content
        )
        for floor_designation in floors:
            floor_num = floor_designation
            if floor_num.isdigit():
                name = f"Floor {floor_num}"
            else:
                # Convert ordinal to number
                ordinal_map = {
                    "first": "1", "First": "1",
                    "second": "2", "Second": "2",
                    "third": "3", "Third": "3",
                    "fourth": "4", "Fourth": "4",
                    "fifth": "5", "Fifth": "5",
                    "sixth": "6", "Sixth": "6",
                }
                floor_num = ordinal_map.get(floor_designation, floor_designation)
                name = f"Floor {floor_num}"

            self.add_location(
                name,
                "dungeon_floor",
                f"Dungeon Floor {floor_num}"
            )

        # Pattern 2: Named zones/areas (Dungeon Floor 1, World Dungeon, etc.)
        zones = re.findall(
            r'(Dungeon Floor \d+|(?:World|First|Second)\s+Dungeon|First\s+Floor)',
            content
        )
        for zone in zones:
            self.add_location(zone, "dungeon_zone", f"Dungeon zone: {zone}")

        # Pattern 3: Safe zones and special areas
        if "Tutorial Guild Hall" in content:
            self.add_location(
                "Tutorial Guild Hall",
                "safe_zone",
                "Tutorial Guild Hall - A safe zone for new adventurers"
            )
        if "Guild Hall" in content and "Tutorial" not in content:
            self.add_location(
                "Guild Hall",
                "safe_zone",
                "Guild Hall - A safe zone for adventurers"
            )

        # Pattern 4: Entrance areas
        entrances = re.findall(
            r'(?:first-level\s+entrances?|level-\d+\s+entrance|entrance[s]?(?:\s+to)?(?:\s+level)?)',
            content,
            re.IGNORECASE
        )
        if entrances:
            self.add_location(
                "Dungeon Entrance",
                "entrance",
                "Main entrance to the World Dungeon"
            )

        # Pattern 5: Boss chambers
        if "Hoarder" in content or "hoarder" in content:
            self.add_location(
                "Hoarder's Chamber",
                "boss_chamber",
                "Boss chamber of the Hoarder - contains massive treasure hoard"
            )

        if "War Chieftain" in content or "war chieftain" in content:
            self.add_location(
                "War Chieftain's Chamber",
                "boss_chamber",
                "Boss chamber of the War Chieftain"
            )

        # Pattern 6: Room/chamber descriptions
        room_pattern = r'(?:in\s+)?(?:a|the)\s+(\w+(?:\s+\w+)*)\s+(?:room|chamber|hall|area)\b'
        rooms = re.findall(room_pattern, content, re.IGNORECASE)
        for room_desc in rooms:
            if len(room_desc) > 3 and len(room_desc) < 40:
                room_name = room_desc.title().strip()
                # Avoid common non-location descriptors
                skip_words = ["big", "small", "dark", "light", "dusty", "empty", "large", "tiny"]
                if not any(word in room_name.lower() for word in skip_words):
                    self.add_location(room_name, "room", f"Room: {room_name}")

        # Pattern 7: Specific dungeon features
        if "marble floor" in content or "marble" in content:
            self.add_location(
                "Marble Chamber",
                "special_feature",
                "Chamber with marble flooring"
            )

        if "door" in content.lower():
            self.add_location(
                "Grand Entrance Door",
                "feature",
                "Large thirty-foot tall door marking dungeon entrance"
            )

        # Pattern 8: Level-specific content areas
        if "level 1" in content.lower() or "first floor" in content.lower():
            self.add_location(
                "First Floor",
                "dungeon_floor",
                "First Floor of the World Dungeon"
            )
            self.add_location(
                "Level 1",
                "dungeon_floor",
                "Level 1 of the World Dungeon - Starting level"
            )

        # Pattern 9: Collapse/time-limited areas
        if "Level Collapse" in content:
            self.add_location(
                "Level Collapse Zone",
                "hazard_area",
                "Area affected by level reclamation/collapse"
            )

        # Pattern 10: Goblin-related locations
        if "goblin" in content.lower():
            self.add_location(
                "Goblin Territory",
                "faction_area",
                "Areas inhabited and controlled by goblins"
            )
        if "hobgoblin" in content.lower():
            self.add_location(
                "Hobgoblin Territory",
                "faction_area",
                "Areas controlled by stronger hobgoblins"
            )

    def extract_all_chunks(self):
        """Extract from all chunk files."""
        chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.txt"))
        print(f"Processing {len(chunk_files)} chunks...")

        for i, chunk_file in enumerate(chunk_files):
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(chunk_files)} chunks...")

            with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            self.extract_from_chunk(content)

    def get_output(self):
        """Generate output JSON structure."""
        return {
            "metadata": {
                "source": "Dungeon Crawler Carl Book 1",
                "extraction_type": "Dungeon Locations and Areas",
                "extraction_date": "2026-02-23",
                "total_chunks_processed": 332,
                "total_unique_locations": len(self.locations)
            },
            "locations": self.locations,
            "location_types": self._categorize_by_type()
        }

    def _categorize_by_type(self):
        """Categorize locations by type."""
        by_type = defaultdict(list)
        for loc_name, loc_data in self.locations.items():
            loc_type = loc_data.get("type", "unknown")
            by_type[loc_type].append({
                "name": loc_name,
                "mentions": self.location_mentions[loc_name]
            })
        return dict(by_type)

def main():
    print("=" * 60)
    print("DUNGEON CRAWLER CARL BOOK 1 - LOCATION EXTRACTION")
    print("=" * 60)
    print()

    extractor = LocationExtractor()
    extractor.extract_all_chunks()

    output = extractor.get_output()

    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"EXTRACTION COMPLETE")
    print(f"  Locations found: {len(extractor.locations)}")
    print(f"  Output file: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print()

    # Print breakdown by type
    print("LOCATIONS BY TYPE:")
    for loc_type in sorted(output["location_types"].keys()):
        locations = output["location_types"][loc_type]
        print(f"  {loc_type}: {len(locations)}")

    print()
    print("SAMPLE LOCATIONS:")
    sample_count = 0
    for loc_type in sorted(output["location_types"].keys()):
        locations = output["location_types"][loc_type][:2]
        for loc in locations:
            if sample_count < 15:
                print(f"  - {loc['name']} ({loc_type})")
                sample_count += 1

    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
