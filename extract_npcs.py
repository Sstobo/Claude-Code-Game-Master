#!/usr/bin/env python3
"""
Extract all NPCs and characters from Dungeon Crawler Carl Book 3 chunks
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

# Directory containing chunks
CHUNKS_DIR = "world-state/campaigns/dungeon-crawler-carl/chunks"
OUTPUT_DIR = "world-state/campaigns/dungeon-crawler-carl/extracted"
OUTPUT_FILE = "npcs.json"

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Track NPCs with context
npcs = {}

# Known character names from Dungeon Crawler Carl
KNOWN_CHARACTERS = {
    "Carl": "Main protagonist, dungeon crawler",
    "Pip": "Carl's companion, small creature",
    "Marjory": "Adventurer, character in the story",
    "Boney": "Skeleton character",
    "Cellica": "Character in the dungeon",
    "Brutus": "Strong character/creature",
    "Greg": "Character name",
}

def is_likely_name(text):
    """Check if text looks like a character name"""
    # Must start with capital letter
    if not text or not text[0].isupper():
        return False
    # Length reasonable for a name
    if len(text) < 2 or len(text) > 50:
        return False
    # Should be mostly letters, possibly with spaces or hyphens
    if not all(c.isalpha() or c.isspace() or c in "'-" for c in text):
        return False
    return True

def extract_npcs_from_text(text, chunk_num):
    """Extract NPC names and descriptions from chunk text"""
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and metadata
        if not line or line.startswith('---') or line.startswith('#'):
            i += 1
            continue

        # Look for patterns like "Name: description"
        if ':' in line and len(line) < 300:
            parts = line.split(':', 1)
            potential_name = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""

            if is_likely_name(potential_name):
                # Add or update NPC
                if potential_name not in npcs:
                    npcs[potential_name] = {
                        "name": potential_name,
                        "descriptions": [],
                        "mentions": [],
                        "roles": set()
                    }

                if chunk_num not in npcs[potential_name]["mentions"]:
                    npcs[potential_name]["mentions"].append(chunk_num)

                if description and description not in npcs[potential_name]["descriptions"]:
                    npcs[potential_name]["descriptions"].append(description)

        # Also track known characters
        for known_name in KNOWN_CHARACTERS.keys():
            if known_name in line and known_name not in npcs:
                npcs[known_name] = {
                    "name": known_name,
                    "descriptions": [KNOWN_CHARACTERS[known_name]],
                    "mentions": [chunk_num],
                    "roles": set()
                }

        i += 1

def main():
    """Process all chunks and extract NPCs"""
    print(f"Reading chunks from {CHUNKS_DIR}...")

    # Get all chunk files
    chunk_files = sorted([f for f in os.listdir(CHUNKS_DIR) if f.startswith('chunk_') and f.endswith('.txt')])
    print(f"Found {len(chunk_files)} chunks")

    # Process each chunk
    for idx, chunk_file in enumerate(chunk_files):
        if idx % 50 == 0:
            print(f"Processing chunk {idx}/{len(chunk_files)}...")

        chunk_path = os.path.join(CHUNKS_DIR, chunk_file)
        try:
            with open(chunk_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                chunk_num = int(chunk_file.replace('chunk_', '').replace('.txt', ''))
                extract_npcs_from_text(content, chunk_num)
        except Exception as e:
            print(f"Error reading {chunk_file}: {e}")

    # Convert to list and sort by name
    npc_list = []
    for name, data in sorted(npcs.items()):
        npc_list.append({
            "name": name,
            "description": " | ".join(data.get("descriptions", [])[:3]),  # First 3 descriptions
            "mentions": sorted(list(set(data.get("mentions", [])))),
            "mention_count": len(set(data.get("mentions", [])))
        })

    # Write output
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "Dungeon Crawler Carl - Book 3",
            "total_npcs": len(npc_list),
            "npcs": npc_list
        }, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete!")
    print(f"Found {len(npc_list)} unique NPCs/characters")
    print(f"Output saved to: {output_path}")

    # Print top characters by mention count
    print("\nTop 30 most mentioned characters:")
    for npc in sorted(npc_list, key=lambda x: x["mention_count"], reverse=True)[:30]:
        print(f"  {npc['name']}: {npc['mention_count']} mentions")

if __name__ == "__main__":
    main()
