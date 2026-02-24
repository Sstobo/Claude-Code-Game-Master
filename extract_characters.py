#!/usr/bin/env python3
"""Extract NPCs and characters from Dungeon Crawler Carl Book 1 chunks"""

import json
import re
from pathlib import Path

chunks_dir = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
all_text = ""
chunk_files = sorted(chunks_dir.glob("chunk_*.txt"))

for chunk_file in chunk_files:
    try:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_text += f.read() + "\n"
    except:
        pass

print(f"Read {len(chunk_files)} chunks")

# Common English words to filter
common_words = {
    'About', 'Above', 'After', 'Again', 'All', 'Also', 'Always', 'And', 'Another',
    'Are', 'Around', 'As', 'At', 'Back', 'Be', 'Because', 'Been', 'Before', 'Being',
    'Between', 'But', 'By', 'Can', 'Come', 'Could', 'Day', 'Did', 'Do', 'Does',
    'Down', 'Each', 'End', 'Even', 'Ever', 'Find', 'First', 'For', 'From', 'Get',
    'Give', 'Go', 'Going', 'Good', 'Got', 'Great', 'Had', 'Has', 'Have', 'He',
    'Head', 'Her', 'Here', 'Him', 'His', 'How', 'If', 'In', 'Into', 'Is', 'It',
    'Its', 'Just', 'Keep', 'Know', 'Last', 'Let', 'Like', 'Long', 'Look', 'Made',
    'Make', 'Man', 'Many', 'May', 'Me', 'Mean', 'More', 'Most', 'Much', 'Must',
    'My', 'Need', 'Never', 'New', 'Next', 'No', 'Not', 'Now', 'Of', 'Off', 'On',
    'One', 'Only', 'Or', 'Other', 'Our', 'Out', 'Over', 'Own', 'Part', 'People',
    'Place', 'Put', 'Said', 'Same', 'See', 'Self', 'She', 'Should', 'Show', 'Side',
    'So', 'Some', 'Something', 'Start', 'Still', 'Such', 'Take', 'Tell', 'Than',
    'That', 'The', 'Their', 'Them', 'Then', 'There', 'These', 'They', 'Thing',
    'Think', 'This', 'Those', 'Though', 'Three', 'Through', 'To', 'Together',
    'Too', 'Took', 'Top', 'Try', 'Two', 'Under', 'Up', 'Use', 'Very', 'Want',
    'Was', 'Way', 'We', 'Well', 'Were', 'What', 'When', 'Where', 'Which', 'While',
    'Who', 'Why', 'Will', 'With', 'Without', 'Woman', 'Work', 'World', 'Would',
    'Year', 'Yes', 'You', 'Your', 'Young'
}

# Known main characters
known_characters = {
    'Carl': {
        'name': 'Carl',
        'role': 'Protagonist',
        'type': 'Human',
        'crawler_id': 4122,
        'description': 'Twenty-seven year old former US Coast Guard marine technician. 6\'3", ~230 lbs. Entered dungeon in pink Crocs and leather jacket.',
        'aliases': []
    },
    'Princess Donut': {
        'name': 'Princess Donut',
        'role': 'Animal Companion',
        'type': 'Cat',
        'crawler_id': 4119,
        'description': 'Tortoiseshell Persian cat. Award-winning show cat companion of Carl.',
        'aliases': ['Donut', 'The Chonk']
    },
    'System': {
        'name': 'System',
        'role': 'Dungeon AI',
        'type': 'Artificial Intelligence',
        'description': 'Dungeon system AI providing notifications and system messages.',
        'aliases': []
    },
    'Mordecai': {
        'name': 'Mordecai',
        'role': 'Tutorial Guide',
        'type': 'Rat-man',
        'description': 'Rat-man NPC who guides Carl through dungeon tutorial.',
        'aliases': []
    },
    'Beatrice': {
        'name': 'Beatrice',
        'role': 'Ex-girlfriend',
        'type': 'Human',
        'description': 'Carl\'s ex-girlfriend, original owner of Princess Donut. Presumed dead.',
        'aliases': ['Bea']
    },
    'Borant Corporation': {
        'name': 'Borant Corporation',
        'role': 'Planetary Regent',
        'type': 'Corporate Entity',
        'description': 'Alien corporation that created the 18-Level World Dungeon.',
        'aliases': ['Borant']
    }
}

npcs = known_characters.copy()

# Extract character names
char_mentions = {}
for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', all_text):
    name = match.group(1)
    if len(name) > 2 and name not in common_words and name not in known_characters:
        char_mentions[name] = char_mentions.get(name, 0) + 1

# Add frequent characters
for name, count in sorted(char_mentions.items(), key=lambda x: x[1], reverse=True)[:50]:
    if name not in npcs and not any(c.isdigit() for c in name):
        desc_match = re.search(
            rf'{re.escape(name)}\s+(?:was|is|were|are|had|has|said|cried|yelled|laughed|called|named)\s+([^.\n]{{10,150}}[.!?])',
            all_text, re.IGNORECASE
        )
        description = desc_match.group(1) if desc_match else f"Character mentioned {count} times."

        npcs[name] = {
            'name': name,
            'role': 'Character',
            'type': 'Unknown',
            'frequency': count,
            'description': description[:200],
            'aliases': []
        }

npcs = dict(sorted(npcs.items()))

output = {
    'source': 'Dungeon Crawler Carl Book 1',
    'book': 'Dungeon Crawler Carl',
    'book_number': 1,
    'author': 'Matt Dinniman',
    'total_npcs': len(npcs),
    'extraction_date': '2026-02-23',
    'npcs': npcs
}

output_dir = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "npcs.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(npcs)} NPCs/characters")
print(f"Output: {output_file}\n")
for i, (name, data) in enumerate(list(npcs.items()), 1):
    print(f"{i:2}. {name:25} | {data['role']:30} | {data['type']}")
