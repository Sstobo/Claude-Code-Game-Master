#!/usr/bin/env python3
"""Extract all items, treasures, equipment from Dungeon Crawler Carl Book 2 chunks."""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

def extract_items_from_chunks(chunks_dir):
    """Read all chunk files and extract item information."""

    items = {}
    chunks_dir = Path(chunks_dir)

    # Read all chunk files
    chunk_files = sorted(chunks_dir.glob("chunk_*.txt"))

    print(f"Reading {len(chunk_files)} chunk files...")

    all_text = []
    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_text.append(f.read())

    full_text = "\n".join(all_text)

    # Comprehensive list of items mentioned in Dungeon Crawler Carl
    # These are specific items found through manual review of the series
    known_items = {
        # Weapons
        'sword': {'type': 'weapon', 'description': 'Bladed weapon'},
        'longsword': {'type': 'weapon', 'description': 'Long bladed weapon'},
        'shortsword': {'type': 'weapon', 'description': 'Short bladed weapon'},
        'broadsword': {'type': 'weapon', 'description': 'Broad bladed weapon'},
        'curved sword': {'type': 'weapon', 'description': 'Curved bladed weapon'},
        'scimitar': {'type': 'weapon', 'description': 'Curved bladed weapon'},
        'axe': {'type': 'weapon', 'description': 'Axe weapon'},
        'battleaxe': {'type': 'weapon', 'description': 'Large battle axe'},
        'greataxe': {'type': 'weapon', 'description': 'Great axe weapon'},
        'double-headed axe': {'type': 'weapon', 'description': 'Axe with two heads'},
        'halberd': {'type': 'weapon', 'description': 'Polearm weapon'},
        'spear': {'type': 'weapon', 'description': 'Polearm weapon'},
        'pike': {'type': 'weapon', 'description': 'Long polearm weapon'},
        'dagger': {'type': 'weapon', 'description': 'Small bladed weapon'},
        'mace': {'type': 'weapon', 'description': 'Blunt weapon'},
        'bow': {'type': 'weapon', 'description': 'Ranged weapon'},
        'crossbow': {'type': 'weapon', 'description': 'Ranged weapon'},
        'arrow': {'type': 'weapon', 'description': 'Projectile for bow'},
        'staff': {'type': 'weapon', 'description': 'Magical staff'},
        'wand': {'type': 'weapon', 'description': 'Magical wand'},
        'club': {'type': 'weapon', 'description': 'Blunt weapon'},
        'flail': {'type': 'weapon', 'description': 'Whipping blunt weapon'},
        'whip': {'type': 'weapon', 'description': 'Whip weapon'},
        'hammer': {'type': 'weapon', 'description': 'Hammer weapon'},
        'javelin': {'type': 'weapon', 'description': 'Thrown weapon'},
        'lance': {'type': 'weapon', 'description': 'Cavalry weapon'},
        'scythe': {'type': 'weapon', 'description': 'Agricultural/weapon'},
        'lightning sword': {'type': 'weapon', 'description': 'Sword made of lightning'},
        'katana': {'type': 'weapon', 'description': 'Curved sword'},

        # Armor
        'armor': {'type': 'armor', 'description': 'Body protection'},
        'plate armor': {'type': 'armor', 'description': 'Metal plate armor'},
        'plate': {'type': 'armor', 'description': 'Metal plate armor'},
        'chain mail': {'type': 'armor', 'description': 'Chain linked armor'},
        'chainmail': {'type': 'armor', 'description': 'Chain linked armor'},
        'leather armor': {'type': 'armor', 'description': 'Leather body protection'},
        'leather': {'type': 'armor', 'description': 'Leather protection'},
        'robe': {'type': 'armor', 'description': 'Long garment'},
        'cloak': {'type': 'armor', 'description': 'Protective cloak'},
        'cape': {'type': 'armor', 'description': 'Flowing cape'},
        'helmet': {'type': 'armor', 'description': 'Head protection'},
        'helm': {'type': 'armor', 'description': 'Head protection'},
        'shield': {'type': 'armor', 'description': 'Defense equipment'},
        'breastplate': {'type': 'armor', 'description': 'Chest armor'},
        'cuirass': {'type': 'armor', 'description': 'Chest and back armor'},
        'gauntlets': {'type': 'armor', 'description': 'Hand protection'},
        'boots': {'type': 'armor', 'description': 'Foot protection'},
        'leotard': {'type': 'armor', 'description': 'Tight fitting garment'},
        'tunic': {'type': 'armor', 'description': 'Long garment'},
        'jerkin': {'type': 'armor', 'description': 'Sleeveless garment'},
        'vest': {'type': 'armor', 'description': 'Upper body garment'},
        'gambeson': {'type': 'armor', 'description': 'Padded armor'},

        # Magic items
        'ring': {'type': 'magic_item', 'description': 'Magical ring'},
        'amulet': {'type': 'magic_item', 'description': 'Magical amulet'},
        'necklace': {'type': 'magic_item', 'description': 'Neck ornament'},
        'talisman': {'type': 'magic_item', 'description': 'Protective charm'},
        'charm': {'type': 'magic_item', 'description': 'Magical charm'},
        'bracelet': {'type': 'magic_item', 'description': 'Arm ornament'},
        'pendant': {'type': 'magic_item', 'description': 'Hanging ornament'},
        'gem': {'type': 'magic_item', 'description': 'Gemstone'},
        'jewel': {'type': 'magic_item', 'description': 'Precious stone'},
        'crystal': {'type': 'magic_item', 'description': 'Crystal stone'},
        'orb': {'type': 'magic_item', 'description': 'Magical sphere'},
        'artifact': {'type': 'magic_item', 'description': 'Magical artifact'},
        'relic': {'type': 'magic_item', 'description': 'Ancient magical item'},

        # Consumables
        'potion': {'type': 'consumable', 'description': 'Magical drinkable'},
        'health potion': {'type': 'consumable', 'description': 'Restores health'},
        'mana potion': {'type': 'consumable', 'description': 'Restores mana'},
        'elixir': {'type': 'consumable', 'description': 'Magical liquid'},
        'salve': {'type': 'consumable', 'description': 'Healing ointment'},
        'ointment': {'type': 'consumable', 'description': 'Healing cream'},
        'herb': {'type': 'consumable', 'description': 'Healing plant'},
        'food': {'type': 'consumable', 'description': 'Edible item'},
        'meat': {'type': 'consumable', 'description': 'Meat food'},
        'bread': {'type': 'consumable', 'description': 'Baked food'},
        'cheese': {'type': 'consumable', 'description': 'Dairy product'},
        'drink': {'type': 'consumable', 'description': 'Beverage'},
        'ale': {'type': 'consumable', 'description': 'Alcoholic drink'},
        'wine': {'type': 'consumable', 'description': 'Alcoholic beverage'},
        'water': {'type': 'consumable', 'description': 'Water'},
        'vodka': {'type': 'consumable', 'description': 'Alcoholic spirit'},
        'moonshine': {'type': 'consumable', 'description': 'Distilled alcohol'},
        'soup': {'type': 'consumable', 'description': 'Liquid food'},
        'hamburger': {'type': 'consumable', 'description': 'Meat sandwich'},
        'apple': {'type': 'consumable', 'description': 'Fruit'},
        'halibut': {'type': 'consumable', 'description': 'Fish'},

        # Currency
        'gold': {'type': 'currency', 'description': 'Gold currency'},
        'gold coin': {'type': 'currency', 'description': 'Gold coin'},
        'silver': {'type': 'currency', 'description': 'Silver currency'},
        'silver coin': {'type': 'currency', 'description': 'Silver coin'},
        'copper': {'type': 'currency', 'description': 'Copper currency'},
        'copper coin': {'type': 'currency', 'description': 'Copper coin'},
        'bronze': {'type': 'currency', 'description': 'Bronze currency'},
        'coin': {'type': 'currency', 'description': 'Currency coin'},

        # Documents
        'map': {'type': 'document', 'description': 'Navigation map'},
        'scroll': {'type': 'document', 'description': 'Written scroll'},
        'book': {'type': 'document', 'description': 'Written book'},
        'grimoire': {'type': 'document', 'description': 'Spell book'},
        'tome': {'type': 'document', 'description': 'Large book'},
        'journal': {'type': 'document', 'description': 'Written journal'},
        'letter': {'type': 'document', 'description': 'Written letter'},
        'note': {'type': 'document', 'description': 'Written note'},
        'blueprint': {'type': 'document', 'description': 'Design plan'},
        'document': {'type': 'document', 'description': 'Written document'},
        'parchment': {'type': 'document', 'description': 'Written parchment'},

        # Equipment/Tools
        'key': {'type': 'equipment', 'description': 'Door key'},
        'rope': {'type': 'equipment', 'description': 'Cordage'},
        'chain': {'type': 'equipment', 'description': 'Metal chain'},
        'grappling hook': {'type': 'equipment', 'description': 'Climbing tool'},
        'lock pick': {'type': 'equipment', 'description': 'Lockpicking tool'},
        'pick': {'type': 'equipment', 'description': 'Digging tool'},
        'shovel': {'type': 'equipment', 'description': 'Digging tool'},
        'spade': {'type': 'equipment', 'description': 'Digging tool'},
        'torch': {'type': 'equipment', 'description': 'Light source'},
        'lantern': {'type': 'equipment', 'description': 'Light source'},
        'candle': {'type': 'equipment', 'description': 'Light source'},
        'light': {'type': 'equipment', 'description': 'Illumination'},
        'flint': {'type': 'equipment', 'description': 'Fire-starting tool'},
        'steel': {'type': 'equipment', 'description': 'Material'},
        'bag': {'type': 'equipment', 'description': 'Container'},
        'pack': {'type': 'equipment', 'description': 'Container'},
        'sack': {'type': 'equipment', 'description': 'Container'},
        'backpack': {'type': 'equipment', 'description': 'Carrying container'},
        'chest': {'type': 'equipment', 'description': 'Storage container'},
        'box': {'type': 'equipment', 'description': 'Container'},
        'case': {'type': 'equipment', 'description': 'Container'},
        'container': {'type': 'equipment', 'description': 'Container'},
        'tool': {'type': 'equipment', 'description': 'Tool'},
        'saw': {'type': 'equipment', 'description': 'Cutting tool'},
        'wheel': {'type': 'equipment', 'description': 'Circular tool'},
        'bowl': {'type': 'equipment', 'description': 'Container'},
        'plate': {'type': 'equipment', 'description': 'Dish'},
        'knife': {'type': 'equipment', 'description': 'Cutting tool'},
    }

    extracted_items = defaultdict(lambda: {
        'name': '',
        'type': '',
        'description': '',
        'context': [],
        'frequency': 0
    })

    # Search for each item in the text
    print("\nSearching for items in text...")
    found_items = {}

    for item_name, item_info in known_items.items():
        # Create a flexible search pattern
        pattern = rf'\b{re.escape(item_name)}\b'
        matches = re.finditer(pattern, full_text, re.IGNORECASE)

        count = 0
        for match in matches:
            count += 1
            # Get surrounding context (100 chars before and after)
            start = max(0, match.start() - 100)
            end = min(len(full_text), match.end() + 100)
            context = full_text[start:end].strip()
            # Clean up context
            context = context.replace('\n', ' ')

            if item_name not in found_items:
                found_items[item_name] = {
                    'name': item_name.title(),
                    'type': item_info['type'],
                    'description': item_info['description'],
                    'contexts': [context],
                    'frequency': 1
                }
            else:
                found_items[item_name]['frequency'] += 1
                if len(found_items[item_name]['contexts']) < 3:
                    found_items[item_name]['contexts'].append(context)

    # Convert to final format
    print(f"\nFound {len(found_items)} unique items.")

    final_items = {}
    for item_key, item_data in found_items.items():
        # Use the first context as the primary description
        primary_context = item_data['contexts'][0][:200] if item_data['contexts'] else ''

        final_items[item_key] = {
            'name': item_data['name'],
            'type': item_data['type'],
            'description': item_data['description'],
            'mentions': item_data['frequency'],
            'context_sample': primary_context
        }

    return final_items


def main():
    chunks_dir = "world-state/campaigns/dungeon-crawler-carl/chunks"
    output_file = "world-state/campaigns/dungeon-crawler-carl/extracted/items.json"

    # Extract items
    items = extract_items_from_chunks(chunks_dir)

    # Create extracted directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Sort items by type then by frequency
    sorted_items = {}
    for item_type in ['weapon', 'armor', 'magic_item', 'currency', 'consumable', 'document', 'equipment', 'miscellaneous']:
        type_items = {k: v for k, v in items.items() if v['type'] == item_type}
        sorted_by_freq = dict(sorted(type_items.items(), key=lambda x: x[1]['mentions'], reverse=True))
        sorted_items.update(sorted_by_freq)

    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_items, f, indent=2, ensure_ascii=False)

    print(f"\nExtracted {len(items)} items to {output_file}")

    # Print summary by type
    type_counts = defaultdict(int)
    for item in items.values():
        type_counts[item['type']] += 1

    print("\nItems by Type:")
    for item_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {item_type}: {count}")

    print("\nTop 25 Most Mentioned Items:")
    sorted_by_freq = sorted(items.items(), key=lambda x: x[1]['mentions'], reverse=True)
    for i, (key, item) in enumerate(sorted_by_freq[:25], 1):
        print(f"  {i:2d}. {item['name']:30s} ({item['type']:15s}) - {item['mentions']:3d} mentions")

if __name__ == "__main__":
    main()
