#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
from collections import defaultdict

chunks_dir = "world-state/campaigns/dungeon-crawler-carl/chunks"
output_dir = "world-state/campaigns/dungeon-crawler-carl/extracted"
output_file = os.path.join(output_dir, "plots.json")

os.makedirs(output_dir, exist_ok=True)

# Data structures
plot_points = []
quests_and_objectives = []
character_arcs = defaultdict(list)
locations_with_details = {}
conflicts_and_antagonists = []
story_themes = defaultdict(list)
key_items_and_artifacts = []
dialogue_exchanges = []
environmental_details = []

chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith('.txt')])
print(f"Processing {len(chunk_files)} chunks for comprehensive extraction...")

# Characters to track
main_characters = {
    'Carl': {'role': 'protagonist', 'class': 'dungeon crawler', 'appearances': 0},
    'Donut': {'role': 'companion', 'class': 'unknown', 'appearances': 0},
    'Mordecai': {'role': 'companion', 'class': 'mage', 'appearances': 0},
    'Rue': {'role': 'ally', 'class': 'unknown', 'appearances': 0},
    'Sigmund': {'role': 'antagonist', 'class': 'unknown', 'appearances': 0},
    'Asha': {'role': 'ally', 'class': 'unknown', 'appearances': 0},
    'Reginald': {'role': 'ally', 'class': 'unknown', 'appearances': 0},
}

all_text = {}
for chunk_file in chunk_files:
    chunk_path = os.path.join(chunks_dir, chunk_file)
    try:
        with open(chunk_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            all_text[chunk_file] = content
    except Exception as e:
        print(f"Error reading {chunk_file}: {e}")

# Process each chunk
chunk_number = 0
for chunk_file, full_content in all_text.items():
    chunk_number += 1
    lines = full_content.split('\n')
    current_page = None
    chapter_num = None

    for line_idx, line in enumerate(lines):
        line_stripped = line.strip()

        # Extract chapter and page info
        if 'Chapter' in line and any(char.isdigit() for char in line):
            chapter_match = re.search(r'Chapter\s+(\d+)', line)
            if chapter_match:
                chapter_num = chapter_match.group(1)

        if '--- Page' in line:
            page_match = re.search(r'--- Page (\d+)', line)
            if page_match:
                current_page = page_match.group(1)

        if not line_stripped or len(line_stripped) < 5:
            continue

        # Track character appearances
        for char_name in main_characters.keys():
            if char_name in line:
                main_characters[char_name]['appearances'] += 1

        # Extract plot points (key story moments)
        plot_keywords = [
            'discovered', 'found', 'realized', 'revealed', 'appeared', 'announced',
            'attacked', 'escaped', 'fought', 'defeated', 'confronted', 'alliance',
            'betrayed', 'alliance broken', 'plot', 'conspiracy', 'secret'
        ]

        for keyword in plot_keywords:
            line_lower = line.lower()
            if keyword in line_lower and len(line) > 30:
                plot_entry = {
                    'chunk': chunk_file,
                    'page': current_page or 'unknown',
                    'chapter': chapter_num or 'unknown',
                    'snippet': line_stripped[:200],
                    'type': 'plot_point',
                    'keyword': keyword
                }
                if plot_entry not in plot_points:
                    plot_points.append(plot_entry)
                break

        # Extract conflicts and antagonists
        conflict_keywords = [
            'enemy', 'enemy forces', 'attack', 'battle', 'war', 'defeat',
            'threat', 'danger', 'monster', 'creature', 'dark', 'evil'
        ]

        for keyword in conflict_keywords:
            if keyword.lower() in line.lower() and len(line) > 40:
                conflict_entry = {
                    'chunk': chunk_file,
                    'page': current_page or 'unknown',
                    'snippet': line_stripped[:250],
                    'type': 'conflict',
                    'keyword': keyword
                }
                if conflict_entry not in conflicts_and_antagonists:
                    conflicts_and_antagonists.append(conflict_entry)
                break

        # Extract locations mentioned
        location_keywords = [
            'tower', 'castle', 'dungeon', 'room', 'chamber', 'hall',
            'street', 'road', 'path', 'area', 'zone', 'level', 'floor',
            'city', 'town', 'village', 'forest', 'mountain', 'cave'
        ]

        for loc_keyword in location_keywords:
            if loc_keyword.lower() in line.lower() and len(line) > 30:
                # Try to extract the location name
                loc_pattern = rf'(?:the|a|at|in|to)\s+([A-Z][a-zA-Z\s]+?{loc_keyword}[a-zA-Z\s]*?)(?:\s+was|\s+is|[,\.]|$)'
                loc_match = re.search(loc_pattern, line, re.IGNORECASE)
                if loc_match:
                    location_name = loc_match.group(1).strip()
                    if location_name not in locations_with_details:
                        locations_with_details[location_name] = {
                            'first_mention': chunk_file,
                            'page': current_page or 'unknown',
                            'mentions': 0,
                            'context': []
                        }
                    locations_with_details[location_name]['mentions'] += 1
                    locations_with_details[location_name]['context'].append(line_stripped[:150])
                break

        # Extract key objectives and quests
        objective_keywords = [
            'must', 'need to', 'have to', 'goal', 'objective', 'mission',
            'task', 'quest', 'find', 'retrieve', 'reach', 'destroy', 'save'
        ]

        for obj_keyword in objective_keywords:
            if obj_keyword.lower() in line.lower() and len(line) > 40:
                quest_entry = {
                    'chunk': chunk_file,
                    'page': current_page or 'unknown',
                    'snippet': line_stripped[:200],
                    'type': 'objective',
                    'keyword': obj_keyword
                }
                if quest_entry not in quests_and_objectives:
                    quests_and_objectives.append(quest_entry)
                break

        # Extract key items and artifacts
        item_keywords = ['item', 'skill', 'ability', 'power', 'magic', 'spell', 'weapon', 'artifact', 'treasure', 'reward']

        for item_keyword in item_keywords:
            if item_keyword.lower() in line.lower() and len(line) > 40:
                item_entry = {
                    'chunk': chunk_file,
                    'page': current_page or 'unknown',
                    'snippet': line_stripped[:200],
                    'type': 'item_or_artifact',
                    'keyword': item_keyword
                }
                if item_entry not in key_items_and_artifacts:
                    key_items_and_artifacts.append(item_entry)
                break

        # Extract dialogue with emotion/intent
        dialogue_pattern = r'([A-Z][a-z]+):\s*["\']([^"\']{15,})["\']'
        dialogue_matches = re.findall(dialogue_pattern, line)
        for speaker, dialogue in dialogue_matches:
            dialogue_entry = {
                'speaker': speaker,
                'dialogue': dialogue[:150],
                'chunk': chunk_file,
                'page': current_page or 'unknown'
            }
            if dialogue_entry not in dialogue_exchanges:
                dialogue_exchanges.append(dialogue_entry)

    if chunk_number % 50 == 0:
        print(f"  Processed {chunk_number}/{len(chunk_files)} chunks...")

# Compile themes from extracted content
all_text_combined = ' '.join(all_text.values()).lower()

themes_to_find = {
    'betrayal': ['betrayal', 'betrayed', 'backstab', 'traitor'],
    'redemption': ['redemption', 'redeem', 'reform', 'change'],
    'power_and_corruption': ['power', 'corrupt', 'corruption', 'dominance'],
    'friendship_and_loyalty': ['friend', 'loyalty', 'loyal', 'trust', 'companion'],
    'survival': ['survive', 'survival', 'death', 'dying', 'alive'],
    'mystery': ['mystery', 'secret', 'hidden', 'unknown', 'puzzle'],
    'danger_and_conflict': ['danger', 'danger', 'threat', 'threat', 'enemy'],
    'sacrifice': ['sacrifice', 'sacrifice', 'give up', 'loss'],
    'growth_and_learning': ['growth', 'learn', 'improve', 'develop'],
}

identified_themes = []
for theme, keywords in themes_to_find.items():
    for keyword in keywords:
        if keyword in all_text_combined:
            identified_themes.append(theme)
            break

# Build comprehensive output
output_data = {
    'metadata': {
        'source': 'Dungeon Crawler Carl Book 2',
        'total_chunks': len(chunk_files),
        'extraction_date': '2026-02-22',
        'extraction_type': 'comprehensive',
        'description': 'Full narrative, quest, and story element extraction from all 282 chunks'
    },
    'summary': {
        'plot_points_found': len(plot_points),
        'quests_objectives_found': len(quests_and_objectives),
        'conflicts_found': len(conflicts_and_antagonists),
        'locations_found': len(locations_with_details),
        'items_found': len(key_items_and_artifacts),
        'dialogue_snippets': len(dialogue_exchanges),
        'identified_themes': len(identified_themes)
    },
    'themes_identified': identified_themes,
    'main_characters': main_characters,
    'plot_points': plot_points[:100],
    'quests_and_objectives': quests_and_objectives[:80],
    'conflicts_and_antagonists': conflicts_and_antagonists[:60],
    'key_items': key_items_and_artifacts[:60],
    'key_locations': dict(list(locations_with_details.items())[:30]),
    'dialogue_samples': dialogue_exchanges[:50]
}

# Write output
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"\nComprehensive extraction complete!")
print(f"  Plot points: {len(plot_points)}")
print(f"  Quests/objectives: {len(quests_and_objectives)}")
print(f"  Conflicts: {len(conflicts_and_antagonists)}")
print(f"  Locations: {len(locations_with_details)}")
print(f"  Items/artifacts: {len(key_items_and_artifacts)}")
print(f"  Dialogue exchanges: {len(dialogue_exchanges)}")
print(f"  Themes: {len(identified_themes)}")
print(f"\nOutput saved to: {output_file}")
