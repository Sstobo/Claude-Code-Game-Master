#!/usr/bin/env python3
"""
Extract all NPCs and characters from Dungeon Crawler Carl Book 3 chunks
"""

import json
import os
import re
from pathlib import Path

# Directory containing chunks
CHUNKS_DIR = "world-state/campaigns/dungeon-crawler-carl/chunks"
OUTPUT_DIR = "world-state/campaigns/dungeon-crawler-carl/extracted"
OUTPUT_FILE = "npcs.json"

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Track NPCs with context
npcs = {}

# Known character names from Dungeon Crawler Carl series
CORE_CHARACTERS = {
    "Carl": {"role": "Protagonist", "type": "Player Character"},
    "Donut": {"role": "Companion", "type": "Sentient Item/Creature"},
    "Elle": {"role": "Character", "type": "NPC"},
    "Pip": {"role": "Companion", "type": "Creature"},
}

# Patterns that indicate system fields to skip
SYSTEM_KEYWORDS = {
    "Warning", "Reward", "Time to Level", "Type", "Environment", 
    "Favorites", "Followers", "Views", "Bounty", "Class", "Leaderboard",
    "Race", "Duration", "Effect", "Note", "Target", "Cost", "Current Mark",
    "Charisma", "Constitution", "Strength", "Dexterity", "Intelligence",
    "Wisdom", "Level", "Experience", "Health", "Mana", "Status", "Condition"
}

def is_system_field(text):
    """Check if text is a system field rather than character name"""
    for keyword in SYSTEM_KEYWORDS:
        if keyword in text:
            return True
    return False

def is_likely_name(text):
    """Check if text looks like a character name"""
    # Must start with capital letter
    if not text or not text[0].isupper():
        return False
    # Length reasonable for a name (2-30 chars typical)
    if len(text) < 2 or len(text) > 30:
        return False
    # Should be mostly letters, possibly with spaces or hyphens
    if not all(c.isalpha() or c.isspace() or c in "'-" for c in text):
        return False
    # Skip system fields
    if is_system_field(text):
        return False
    return True

def extract_npcs_from_text(text, chunk_num):
    """Extract NPC names and descriptions from chunk text"""
    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        # Skip empty lines and metadata
        if not line or line.startswith('---') or line.startswith('#') or line.startswith('Page'):
            continue

        # Look for patterns like "Name: description"
        if ':' in line and len(line) < 400:
            parts = line.split(':', 1)
            potential_name = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""

            if is_likely_name(potential_name) and len(description) > 5:
                # Add or update NPC
                if potential_name not in npcs:
                    npcs[potential_name] = {
                        "name": potential_name,
                        "descriptions": [],
                        "mentions": set(),
                        "type": "NPC"
                    }

                npcs[potential_name]["mentions"].add(chunk_num)

                # Avoid duplicate descriptions
                if description not in npcs[potential_name]["descriptions"]:
                    npcs[potential_name]["descriptions"].append(description)

        # Also track core characters when mentioned
        for known_name, info in CORE_CHARACTERS.items():
            # Simple word boundary check
            if f" {known_name} " in f" {line} " and known_name not in npcs:
                npcs[known_name] = {
                    "name": known_name,
                    "descriptions": [info.get("role", "Character")],
                    "mentions": {chunk_num},
                    "type": info.get("type", "NPC")
                }

def main():
    """Process all chunks and extract NPCs"""
    print(f"Reading chunks from {CHUNKS_DIR}...")

    # Get all chunk files
    chunk_files = sorted([f for f in os.listdir(CHUNKS_DIR) if f.startswith('chunk_') and f.endswith('.txt')])
    print(f"Found {len(chunk_files)} chunks\n")

    # Process each chunk
    for idx, chunk_file in enumerate(chunk_files):
        if idx % 100 == 0 and idx > 0:
            print(f"  Processed {idx} chunks...")

        chunk_path = os.path.join(CHUNKS_DIR, chunk_file)
        try:
            with open(chunk_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                chunk_num = int(chunk_file.replace('chunk_', '').replace('.txt', ''))
                extract_npcs_from_text(content, chunk_num)
        except Exception as e:
            pass  # Silently skip errors

    # Convert to list and sort by mention count
    npc_list = []
    for name, data in npcs.items():
        mention_list = sorted(list(data.get("mentions", set())))
        descriptions = data.get("descriptions", [])
        
        npc_list.append({
            "name": name,
            "type": data.get("type", "NPC"),
            "description": descriptions[0] if descriptions else "Character from the book",
            "mentions_in_chunks": mention_list,
            "mention_count": len(mention_list),
            "context_snippets": descriptions[:2]  # First 2 unique descriptions
        })

    # Sort by mention count
    npc_list = sorted(npc_list, key=lambda x: x["mention_count"], reverse=True)

    # Write output
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "Dungeon Crawler Carl - Book 3 (The Dungeon Anarchist's Cookbook)",
            "extraction_date": "2026-02-22",
            "total_chunks": len(chunk_files),
            "total_npcs": len(npc_list),
            "npcs": npc_list
        }, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete!")
    print(f"Found {len(npc_list)} unique NPCs/characters")
    print(f"Output saved to: {output_path}\n")

    # Print top characters by mention count
    print("Top 25 most mentioned characters:")
    for npc in npc_list[:25]:
        print(f"  {npc['name']:20} | Type: {npc['type']:20} | Mentions: {npc['mention_count']:3}")

if __name__ == "__main__":
    main()
