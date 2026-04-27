#!/usr/bin/env python3
"""
Extract all items, treasures, equipment, weapons, and objects from DCC Book 2 chunks.
Focuses on the most reliable item name patterns and reduces false positives.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

def categorize_item(item_name):
    """Categorize items by type."""
    item_lower = item_name.lower()

    weapon_keywords = ['sword', 'axe', 'bow', 'spear', 'dagger', 'mace', 'hammer', 'staff', 'wand', 'blade', 'pike', 'halberd', 'flail', 'scythe', 'musket', 'rifle', 'gun', 'crossbow', 'club', 'cudgel', 'lance', 'bearer']
    armor_keywords = ['armor', 'shield', 'helmet', 'boots', 'gloves', 'cloak', 'robe', 'tunic', 'breastplate', 'chainmail', 'plate', 'cuirass', 'gauntlets', 'leggings', 'gorget', 'mail', 'leather', 'cloth', 'jerkin', 'vest', 'coat', 'vestplate', 'chestplate', 'pauldrons', 'greaves', 'vambraces']
    magical_keywords = ['potion', 'scroll', 'tome', 'grimoire', 'crystal', 'gem', 'jewel', 'artifact', 'relic', 'talisman', 'charm', 'enchanted', 'magical', 'cursed', 'blessed', 'spell', 'ward', 'hex', 'curse', 'boon', 'enchantment', 'incantation', 'medallion', 'orb', 'box']
    accessory_keywords = ['ring', 'amulet', 'pendant', 'necklace', 'bracelet', 'gauntlet', 'crown', 'tiara', 'circlet', 'brooch', 'clasp', 'earring', 'locket', 'anklet', 'torque']
    tool_keywords = ['rope', 'torch', 'lantern', 'pick', 'shovel', 'crowbar', 'lockpick', 'key', 'chest', 'bag', 'sack', 'case', 'bottle', 'flask', 'canteen', 'map', 'compass', 'bedroll', 'tent', 'quill', 'ink', 'parchment', 'ledger', 'journal', 'knife', 'saw', 'wrench', 'chain', 'grapple', 'hook', 'bucket', 'vial', 'container', 'backpack', 'pack', 'pouch', 'purse']
    treasure_keywords = ['gold', 'silver', 'copper', 'coin', 'piece', 'treasure', 'jewels', 'riches', 'wealth', 'bounty', 'loot', 'fortune', 'nugget', 'bullion', 'ore', 'ingot', 'pearl', 'diamond']

    for word in weapon_keywords:
        if word in item_lower:
            return 'Weapon'
    for word in armor_keywords:
        if word in item_lower:
            return 'Armor/Equipment'
    for word in magical_keywords:
        if word in item_lower:
            return 'Magical Item'
    for word in accessory_keywords:
        if word in item_lower:
            return 'Accessory'
    for word in tool_keywords:
        if word in item_lower:
            return 'Tool/Misc'
    for word in treasure_keywords:
        if word in item_lower:
            return 'Treasure'

    return 'Item'

def extract_items_from_chunks(chunks_dir):
    """
    Extract items using multiple patterns:
    1. Multi-word item patterns like "[Adjective] [Item Type]"
    2. Capitalized item names with item type suffixes
    3. Equipment/item mentions in specific contexts
    """
    items_dict = {}
    chunk_files = sorted(chunks_dir.glob('chunk_*.txt'), key=lambda x: int(x.stem.split('_')[1]))

    print(f"Processing {len(chunk_files)} chunk files...")

    # Pattern 1: "[Word] [ItemType]" - most reliable
    item_type_suffixes = ['Armor', 'Shield', 'Helmet', 'Boots', 'Gloves', 'Cloak', 'Robe', 'Sword', 'Axe', 'Bow', 'Spear', 'Dagger', 'Mace', 'Hammer', 'Staff', 'Wand', 'Potion', 'Scroll', 'Gem', 'Jewel', 'Artifact', 'Relic', 'Ring', 'Amulet', 'Pendant', 'Necklace', 'Bracelet', 'Crown', 'Tiara', 'Circlet', 'Brooch', 'Charm', 'Talisman', 'Orb', 'Crystal', 'Case', 'Spell', 'Box', 'Grail', 'Tome', 'Grimoire', 'Gauntlets', 'Tunic', 'Blade', 'Lance', 'Club', 'Crossbow', 'Pick', 'Lantern', 'Torch', 'Chest', 'Flask', 'Canteen', 'Bag', 'Sack', 'Compass', 'Map', 'Quill', 'Wand', 'Bearer']

    for chunk_idx, chunk_file in enumerate(chunk_files):
        if chunk_idx % 50 == 0:
            print(f"  Processing chunk {chunk_idx}/{len(chunk_files)}...")

        try:
            with open(chunk_file, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                chunk_name = chunk_file.name

                # Pattern: Multi-word items like "Wisp Armor", "Earth Hobby Potion", "Nightgaunt Cloak"
                for suffix in item_type_suffixes:
                    # Match "[Capital Word(s)] [ItemType]"
                    pattern = rf'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+{suffix}\b'
                    matches = re.finditer(pattern, text)

                    for match in matches:
                        item_name = f"{match.group(1)} {suffix}"
                        item_key = item_name.lower()

                        # Get context
                        start = max(0, match.start() - 80)
                        end = min(len(text), match.end() + 80)
                        context_snippet = text[start:end].replace('\n', ' ').strip()
                        if len(context_snippet) > 150:
                            context_snippet = context_snippet[:150] + "..."

                        if item_key not in items_dict:
                            items_dict[item_key] = {
                                'name': item_name,
                                'type': categorize_item(item_name),
                                'first_found_chunk': chunk_name,
                                'occurrences': 1,
                                'contexts': [context_snippet]
                            }
                        else:
                            items_dict[item_key]['occurrences'] += 1
                            if context_snippet not in items_dict[item_key]['contexts']:
                                items_dict[item_key]['contexts'].append(context_snippet)

                # Pattern 2: Standalone known item types (from explicit game text)
                special_items = [
                    'Hobby Potion', 'Fan Box', 'Quest Box', 'Earth Box', 'Silver Box',
                    'Gold Box', 'Dropper Spell', 'Undead Spell', 'Turn Undead Spell',
                    'Panty Dropper Spell', 'Upgrade Scroll', 'Magical Fervor',
                    'Glass Reaper Case', 'Recruitment Wand', 'Torch Spell',
                    'Desperado Club', 'Plot Armor', 'Nightgaunt Cloak',
                    'Wisp Armor', 'Sepsis Crown', 'Earth Hobby Potion',
                    'BigBoi Boxers', 'Caps of the Expectorating Tizheruk',
                    'Sheol Glass Reaper Case'
                ]

                for item_name in special_items:
                    pattern = re.escape(item_name)
                    matches = re.finditer(pattern, text)

                    for match in matches:
                        item_key = item_name.lower()

                        start = max(0, match.start() - 80)
                        end = min(len(text), match.end() + 80)
                        context_snippet = text[start:end].replace('\n', ' ').strip()
                        if len(context_snippet) > 150:
                            context_snippet = context_snippet[:150] + "..."

                        if item_key not in items_dict:
                            items_dict[item_key] = {
                                'name': item_name,
                                'type': categorize_item(item_name),
                                'first_found_chunk': chunk_name,
                                'occurrences': 1,
                                'contexts': [context_snippet]
                            }
                        else:
                            items_dict[item_key]['occurrences'] += 1
                            if context_snippet not in items_dict[item_key]['contexts']:
                                items_dict[item_key]['contexts'].append(context_snippet)

        except Exception as e:
            print(f"Error reading {chunk_file}: {e}")
            continue

    return items_dict

def main():
    chunks_dir = Path('world-state/campaigns/dungeon-crawler-carl/chunks')
    output_dir = Path('world-state/campaigns/dungeon-crawler-carl/extracted')
    output_file = output_dir / 'items.json'

    print(f"Reading chunks from {chunks_dir}...")

    if not chunks_dir.exists():
        print(f"ERROR: Chunks directory not found: {chunks_dir}")
        return

    items_dict = extract_items_from_chunks(chunks_dir)

    # Sort items by name
    items_list = sorted(items_dict.values(), key=lambda x: x['name'])

    # Create final structure
    output = {
        'source': 'Dungeon Crawler Carl - Book 2',
        'extraction_date': '2026-02-23',
        'total_unique_items': len(items_list),
        'items': items_list
    }

    # Write to JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete!")
    print(f"Total unique items: {len(items_list)}")
    print(f"Output file: {output_file.absolute()}")

    # Print summary by type
    type_counts = defaultdict(int)
    total_occurrences = 0
    for item in items_list:
        type_counts[item['type']] += 1
        total_occurrences += item['occurrences']

    print(f"Total occurrences: {total_occurrences}")
    print("\nItems by type:")
    for item_type in sorted(type_counts.keys()):
        count = type_counts[item_type]
        print(f"  {item_type}: {count}")

    # Print all items
    print("\nAll extracted items:")
    for item in items_list:
        if item['type'] != 'Item':
            print(f"  - {item['name']:40s} ({item['type']:20s}) - {item['occurrences']} occurrences")

if __name__ == '__main__':
    main()
