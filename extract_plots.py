from pathlib import Path
import json
import re
from collections import defaultdict

chunks_dir = Path("world-state/campaigns/dungeon-crawler-carl/chunks")
output_dir = Path("world-state/campaigns/dungeon-crawler-carl/extracted")
output_file = output_dir / "plots.json"

output_dir.mkdir(parents=True, exist_ok=True)

# Read all chunks
chunk_files = sorted(chunks_dir.glob("chunk_*.txt"))
print(f"Found {len(chunk_files)} chunks to process...\n")

all_text = ""
for i, chunk_file in enumerate(chunk_files):
    try:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            all_text += content + "\n\n"
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1} chunks...")
    except Exception as e:
        print(f"Error reading {chunk_file}: {e}")

print(f"Total text processed: {len(all_text)} characters\n")

# THEMES
theme_keywords = {
    "leveling_progression": ["level", "experience", "progression", "upgrade", "xp"],
    "survival_combat": ["dungeon", "monster", "combat", "danger", "trap", "fight"],
    "friendship_bonds": ["bond", "friendship", "companion", "team", "ally"],
    "mystery_secrets": ["secret", "mystery", "revelation", "discover", "hidden"],
    "power_ability": ["power", "ability", "skill", "strength"],
    "growth_learning": ["grow", "mature", "learn", "wisdom"],
    "determination": ["determination", "will", "persist", "overcome"],
    "system_mechanics": ["system", "game", "mechanic", "rule"],
    "sacrifice": ["sacrifice", "loss", "death"],
    "humor": ["funny", "joke", "laugh", "humor"]
}

themes = set()
for theme, keywords in theme_keywords.items():
    for keyword in keywords:
        if keyword.lower() in all_text.lower():
            themes.add(theme)
            break

print(f"Identified themes: {', '.join(sorted(themes))}\n")

# CHARACTERS
char_patterns = [
    r'\b(Carl|Donut|Mordecai|Raja|Max|Maranda|Timmy|Drake|Kess|Seya|Ulli|Geneva|Oren|Silara|Grimjaw|Celeste|Daltus|Kamros|Luckystone|Alchemy|Beth)\b',
]

characters = set()
for pattern in char_patterns:
    matches = re.findall(pattern, all_text)
    characters.update(matches)

characters = sorted(list(characters))
print(f"Identified {len(characters)} characters\n")

# LOCATIONS
location_patterns = [
    r'(?:Borant\'s|Dungeon|in|at|entered)\s+([A-Z][a-z\s]+(?:Dungeon|Floor|Level|Zone|Chamber|Hall|Area|City|Town|Forest|Cave|Tower|Plane|Realm|Crypt))',
]

locations = set()
for pattern in location_patterns:
    matches = re.findall(pattern, all_text, re.IGNORECASE)
    locations.update(matches)

locations = sorted(list(locations))[:100]
print(f"Identified {len(locations)} locations\n")

# QUESTS
quest_patterns = [
    (r'(?:need|must|should|goal|objective|mission)\s+(?:to|is\s+to)\s+([^.!?\n]{15,180})', 'objective'),
    (r'(?:Find|Recover|Retrieve|Obtain|Defeat|Rescue|Explore|Discover|Kill|Escape|Survive)\s+([^.!?\n]{15,180})', 'action_task'),
]

extracted_quests = set()
quests = []
for pattern, qtype in quest_patterns:
    matches = re.finditer(pattern, all_text, re.IGNORECASE)
    for match in matches:
        quest_text = match.group(1).strip()
        quest_text = re.sub(r'\s+', ' ', quest_text)
        if len(quest_text) > 15 and len(quest_text) < 180 and quest_text not in extracted_quests:
            extracted_quests.add(quest_text)
            quests.append({
                "description": quest_text,
                "type": qtype,
                "status": "discovered",
                "importance": "medium"
            })

print(f"Extracted {len(quests)} unique quests\n")

# PLOT HOOKS
plot_keywords = [
    ("mystery", r'(?:mystery|secret|hidden|unknown|discover|reveal)\b'),
    ("threat", r'(?:danger|threat|enemy|attack|monster|creature)\b'),
    ("opportunity", r'(?:opportunity|chance|found|treasure|reward)\b'),
    ("conflict", r'(?:conflict|war|battle|fight|struggle)\b'),
    ("loss", r'(?:lose|lost|death|died|sacrifice)\b'),
    ("gain", r'(?:gain|earned|found|obtained|reward)\b'),
    ("growth", r'(?:growth|progress|advance|improve)\b'),
    ("wisdom", r'(?:wisdom|lesson|learning|understand|realize)\b'),
]

hook_snippets = set()
plot_hooks = []
for plot_type, pattern in plot_keywords:
    matches = list(re.finditer(pattern, all_text, re.IGNORECASE))[:12]
    for match in matches:
        start = max(0, match.start() - 100)
        end = min(len(all_text), match.end() + 100)
        context = all_text[start:end].replace('\n', ' ').strip()
        if len(context) > 40 and len(context) < 300 and context not in hook_snippets:
            hook_snippets.add(context)
            plot_hooks.append({
                "type": plot_type,
                "snippet": context,
                "prominence": "discovered"
            })

print(f"Extracted {len(plot_hooks)} plot hooks\n")

# NARRATIVE SCENES
paragraphs = all_text.split('\n\n')
scene_keywords = ['carl', 'dungeon', 'combat', 'said', 'realized', 'learned']
scenes = []
for para in paragraphs:
    if len(para) > 200 and any(word in para.lower() for word in scene_keywords):
        cleaned = para.replace('\n', ' ').strip()
        scenes.append({
            "description": cleaned[:500],
            "type": "narrative_scene"
        })
        if len(scenes) >= 80:
            break

print(f"Extracted {len(scenes)} narrative scenes\n")

# Build output
plot_data = {
    "metadata": {
        "source": "Dungeon Crawler Carl Book 2",
        "chunks_processed": len(chunk_files),
        "extraction_date": "2026-02-23",
        "total_text_processed": len(all_text),
        "extraction_method": "pattern-based NLP"
    },
    "major_themes": sorted(list(themes)),
    "primary_characters": characters,
    "discovered_locations": locations,
    "quests": {
        "total_count": len(quests),
        "quests": quests[:150]
    },
    "plot_hooks": {
        "total_count": len(plot_hooks),
        "hooks": plot_hooks[:120]
    },
    "narrative_scenes": {
        "total_count": len(scenes),
        "scenes": scenes[:80]
    },
    "storyline_summary": {
        "description": "Extracted from Dungeon Crawler Carl Book 2",
        "book": 2,
        "tone": "dark_comedy_progression_fantasy"
    }
}

# Write output
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(plot_data, f, indent=2, ensure_ascii=False)

print("="*70)
print("EXTRACTION COMPLETE")
print("="*70)
print(f"Themes: {len(plot_data['major_themes'])}")
print(f"Characters: {len(plot_data['primary_characters'])}")
print(f"Locations: {len(plot_data['discovered_locations'])}")
print(f"Quests: {plot_data['quests']['total_count']}")
print(f"Plot hooks: {plot_data['plot_hooks']['total_count']}")
print(f"Scenes: {plot_data['narrative_scenes']['total_count']}")
print(f"\nOutput: {output_file}")
print("="*70)
