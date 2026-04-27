#!/usr/bin/env python3
"""
Extract all NPCs and characters from Dungeon Crawler Carl Book 3 chunks
More refined to avoid false positives
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
    "Carl": {"role": "Protagonist, Dungeon Crawler", "type": "Player Character"},
    "Donut": {"role": "Carl's companion, sentient item", "type": "Sentient Item"},
    "Elle": {"role": "Female character, adventurer", "type": "Character"},
    "Pip": {"role": "Companion creature", "type": "Creature"},
    "Imani": {"role": "Female character", "type": "Character"},
    "Zev": {"role": "Male character", "type": "Character"},
}

# Words/patterns that are definitely NOT character names
EXCLUDED_WORDS = {
    "Warning", "Reward", "Time", "Type", "Environment", "Favorites", "Followers", 
    "Views", "Bounty", "Class", "Leaderboard", "Race", "Duration", "Effect", "Note", 
    "Target", "Cost", "Current", "Strength", "Dexterity", "Intelligence", "Wisdom",
    "Constitution", "Charisma", "Level", "Experience", "Health", "Mana", "Status", 
    "Condition", "Rental", "Taxes", "Sponsors", "Failure", "Collapse", "Cooldown",
    "Price", "Wetware", "Damage", "Armor", "Attack", "Defense", "Skill", "Ability",
    "Description", "Rules", "Example", "Chapter", "Page", "Section", "Introduction",
    "Summary", "Conclusion", "Author", "Title", "Contents", "Index", "Appendix",
    "Reference", "Glossary", "Bibliography", "Permissions", "Copyright", "License",
    "Permission", "All rights", "Edited by", "Illustrated by", "Design by"
}

def is_excluded(text):
    """Check if text should be excluded"""
    text_lower = text.lower()
    for excluded in EXCLUDED_WORDS:
        if excluded.lower() in text_lower:
            return True
    # Avoid multi-word system fields
    if len(text.split()) > 3:
        return True
    return False

def looks_like_real_name(text):
    """Check if text looks like a real person/character name"""
    if not text or len(text) < 2 or len(text) > 25:
        return False
    if is_excluded(text):
        return False
    # First letter must be uppercase
    if not text[0].isupper():
        return False
    # Should contain only letters, spaces, hyphens, apostrophes
    if not all(c.isalpha() or c.isspace() or c in "'-" for c in text):
        return False
    # At least 50% of non-space chars should be letters
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < len(text) * 0.5:
        return False
    return True

def extract_npcs_from_text(text, chunk_num):
    """Extract NPC names and descriptions from chunk text"""
    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        # Skip empty lines, page markers, and headers
        if not line or line.startswith('---') or line.startswith('#') or 'Page' in line:
            continue

        # Skip if it's clearly metadata (all caps short lines)
        if line.isupper() and len(line) < 20:
            continue

        # Look for patterns like "Name: description"
        if ':' in line and len(line) < 200:
            parts = line.split(':', 1)
            potential_name = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""

            # Only accept if it looks like a real name
            if looks_like_real_name(potential_name) and len(description) > 10:
                if potential_name not in npcs:
                    npcs[potential_name] = {
                        "name": potential_name,
                        "descriptions": [],
                        "mentions": set(),
                        "type": "NPC"
                    }

                npcs[potential_name]["mentions"].add(chunk_num)

                # Add unique descriptions
                if description not in npcs[potential_name]["descriptions"]:
                    npcs[potential_name]["descriptions"].append(description)

def main():
    """Process all chunks and extract NPCs"""
    print(f"Reading chunks from {CHUNKS_DIR}...")

    # Get all chunk files
    chunk_files = sorted([f for f in os.listdir(CHUNKS_DIR) if f.startswith('chunk_') and f.endswith('.txt')])
    print(f"Found {len(chunk_files)} chunks\n")

    # First pass: add known characters
    for name, info in CORE_CHARACTERS.items():
        npcs[name] = {
            "name": name,
            "descriptions": [info["role"]],
            "mentions": set(),
            "type": info["type"]
        }

    # Second pass: extract from text
    for idx, chunk_file in enumerate(chunk_files):
        if idx % 100 == 0 and idx > 0:
            print(f"  Processed {idx} chunks...")

        chunk_path = os.path.join(CHUNKS_DIR, chunk_file)
        try:
            with open(chunk_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                chunk_num = int(chunk_file.replace('chunk_', '').replace('.txt', ''))
                extract_npcs_from_text(content, chunk_num)
                
                # Also look for core characters in raw text
                for known_name in CORE_CHARACTERS.keys():
                    if known_name in content:
                        npcs[known_name]["mentions"].add(chunk_num)
        except Exception as e:
            pass

    # Convert to list and sort by mention count
    npc_list = []
    for name, data in npcs.items():
        mention_list = sorted(list(data.get("mentions", set())))
        descriptions = data.get("descriptions", [])
        
        npc_list.append({
            "name": name,
            "type": data.get("type", "NPC"),
            "description": descriptions[0] if descriptions else "",
            "additional_context": descriptions[1:] if len(descriptions) > 1 else [],
            "mentions_in_chunks": mention_list,
            "mention_count": len(mention_list)
        })

    # Sort by mention count
    npc_list = sorted(npc_list, key=lambda x: x["mention_count"], reverse=True)

    # Remove duplicates and clean
    seen = set()
    clean_list = []
    for npc in npc_list:
        name_lower = npc["name"].lower()
        if name_lower not in seen:
            seen.add(name_lower)
            clean_list.append(npc)

    # Write output
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "Dungeon Crawler Carl - Book 3 (The Dungeon Anarchist's Cookbook)",
            "extraction_date": "2026-02-22",
            "total_chunks": len(chunk_files),
            "total_npcs": len(clean_list),
            "npcs": clean_list
        }, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete!")
    print(f"Found {len(clean_list)} unique NPCs/characters")
    print(f"Output saved to: {output_path}\n")

    # Print all characters
    print("All extracted characters:")
    for npc in clean_list:
        desc = npc["description"][:60] + "..." if len(npc["description"]) > 60 else npc["description"]
        print(f"  {npc['name']:20} | {npc['type']:20} | Mentions: {npc['mention_count']:3} | {desc}")

if __name__ == "__main__":
    main()
