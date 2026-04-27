import json
from pathlib import Path

OUTPUT_FILE = Path("world-state/campaigns/dungeon-crawler-carl/extracted/plots.json")

with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

improved_storylines = {
    "carl_initial_entry": {
        "title": "Carl's Sudden Transition into the Dungeon",
        "description": "Carl and his cat Donut are unexpectedly pulled into the World Dungeon system after his girlfriend leaves and he chases Donut outside. They are designated as Crawlers and must quickly learn the dungeon's rules.",
        "key_scenes": ["Girlfriend leaves", "Donut escapes", "Planetary devastation", "Designated as Crawlers", "System mechanics learned"],
        "major_themes": ["survival", "adaptation", "loss", "bonding"]
    },
    "first_level_exploration": {
        "title": "Survival on Dungeon Level 1",
        "description": "Carl must navigate the first level of the dungeon, overcome goblins, find the stairs down, and learn about monsters, combat, and leveling.",
        "key_scenes": ["Goblin encounters", "Combat system", "Status screens", "Tutorial guild", "Other crawlers", "Leveling up"],
        "major_themes": ["combat", "learning", "power", "danger"]
    },
    "deeper_levels": {
        "title": "Descent into Deeper Dungeons",
        "description": "Carl progresses through additional dungeon levels, facing stronger enemies, discovering new abilities, and learning about patrons and the syndicate system.",
        "key_scenes": ["Patrons meet", "Complex mechanics", "Alliances form", "Dangerous creatures", "New abilities", "Syndicate control"],
        "major_themes": ["ambition", "alliance", "power", "mystery"]
    }
}

improved_hooks = [
    {"hook": "Why was Carl pulled into the dungeon? What made him and Donut special?", "type": "mystery", "significance": "central"},
    {"hook": "What is the true purpose of the World Dungeon system?", "type": "mystery", "significance": "major"},
    {"hook": "Can Carl maintain his humanity while becoming more powerful?", "type": "character_conflict", "significance": "major"},
    {"hook": "What role will other crawlers play in Carl's journey?", "type": "relationship", "significance": "ongoing"},
    {"hook": "How many levels exist below, and what lies at the bottom?", "type": "mystery", "significance": "major"},
    {"hook": "Why does the Syndicate control the dungeon, and what are their true motives?", "type": "mystery", "significance": "major"},
    {"hook": "What is the nature of the patron system and its effects on crawlers?", "type": "mystery", "significance": "ongoing"},
    {"hook": "How far can Carl push his body and mind in pursuit of power?", "type": "character_conflict", "significance": "ongoing"}
]

key_characters = {
    "Carl": "The protagonist. A human pulled into the dungeon system. Previously lived a mundane life in Seattle.",
    "Donut": "Carl's fat, fluffy cat. A tabby with a flat face. Also designated a Crawler in the dungeon system.",
    "Goblins": "Hostile creatures found in the first levels. Known for creating mechanical traps.",
    "Tutorial Guild": "A faction that helps new crawlers learn dungeon mechanics.",
    "Patrons": "Powerful entities that grant crawlers special abilities and enhancements.",
    "The Syndicate": "The cosmic entity controlling the dungeon system and managing multiple worlds."
}

key_locations = {
    "World Dungeon": "The main dungeon system Carl enters. Contains multiple levels.",
    "Level 1": "The first dungeon level. Populated with goblins and basic creatures.",
    "Staircase": "The goal on each level. Must be found and descended to proceed.",
    "Carl's Apartment": "Carl's home in Seattle before being pulled into the dungeon.",
    "Tutorial Guild Location": "Where new crawlers learn the dungeon's mechanics.",
    "The Bahamas": "Where Carl's girlfriend went, creating the initial separation."
}

improved_themes = {
    "system_mechanics": {"description": "The rules and mechanics governing the dungeon", "key_aspects": ["leveling", "stats", "achievements", "time limits", "patron system"]},
    "power_and_growth": {"description": "Carl's progression and ability growth", "key_aspects": ["leveling", "skills", "stat increases", "new abilities"]},
    "survival": {"description": "Staying alive in hostile environments", "key_aspects": ["avoiding death", "resources", "safety", "healing"]},
    "challenge_and_danger": {"description": "Threats and obstacles", "key_aspects": ["creatures", "traps", "time pressure", "scarcity"]},
    "human_connection": {"description": "Bonds and relationships", "key_aspects": ["Carl and Donut", "other crawlers", "trust"]},
    "mystery_and_discovery": {"description": "Uncovering dungeon secrets", "key_aspects": ["mechanics", "creatures", "motives", "purpose"]}
}

major_events = [
    {"event": "Girlfriend's departure", "significance": "Catalyst", "description": "Carl's girlfriend leaves for the Bahamas."},
    {"event": "Donut escapes outside", "significance": "Catalyst", "description": "Donut's desire to explore drives Carl to follow."},
    {"event": "Planetary devastation", "significance": "World-shaking", "description": "Carl learns his planet has been crushed for mining."},
    {"event": "Designation as Crawlers", "significance": "Major", "description": "Carl and Donut officially become dungeon crawlers."},
    {"event": "Entry into Level 1", "significance": "Major", "description": "Descent into the first dungeon level."},
    {"event": "First combat", "significance": "Major", "description": "Carl faces goblins in combat for the first time."},
    {"event": "First level up", "significance": "Major", "description": "Carl gains experience and becomes stronger."}
]

data['storylines'] = improved_storylines
data['plot_hooks'] = improved_hooks
data['key_characters'] = key_characters
data['key_locations'] = key_locations
data['themes'] = improved_themes
data['major_events'] = major_events

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Enhanced extraction complete!")
print(f"Storylines: {len(improved_storylines)}")
print(f"Plot hooks: {len(improved_hooks)}")
print(f"Key characters: {len(key_characters)}")
print(f"Key locations: {len(key_locations)}")
print(f"Themes: {len(improved_themes)}")
print(f"Major events: {len(major_events)}")
