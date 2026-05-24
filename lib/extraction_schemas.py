#!/usr/bin/env python3
"""
JSON schemas for D&D content extraction
Defines exact structure for agent outputs
"""

# NPC Schema - For character extraction
NPC_SCHEMA = {
    "name": "",  # Required, max 100 chars
    "description": "",  # 80+ words narrative description
    "attitude": "",  # enum: friendly/neutral/hostile/suspicious/helpful
    "location_tags": [],  # Where they appear in the module
    "events": [],  # Optional: notable events or quests
    "stats": {},  # Opaque ruleset-specific stats — extractors emit whatever they find
    "dialogue": [],  # Optional: notable quotes or conversation topics
    "source": ""  # Document name/section
}

# Location Schema - For place extraction
LOCATION_SCHEMA = {
    "name": "",  # Required location name
    "position": "",  # Relative position or coordinates
    "description": "",  # Rich narrative description
    "connections": [],  # [{to: name, path: description}]
    "features": [],  # Notable features or areas within
    "inhabitants": [],  # NPCs or creatures found here
    "hazards": [],  # Traps, environmental dangers
    "notes": "",  # Optional special features or secrets
    "source": ""  # Document name/section
}

# Item Schema - For treasure/equipment extraction
ITEM_SCHEMA = {
    "name": "",  # Item name
    "description": "",  # Physical and narrative description
    "type": "",  # weapon/armor/potion/scroll/wondrous/etc
    "rarity": "",  # common/uncommon/rare/very rare/legendary/artifact
    "mechanics": "",  # Game mechanics and effects
    "value": "",  # GP value if specified
    "location": "",  # Where found in module
    "attunement": False,  # Requires attunement?
    "cursed": False,  # Is it cursed?
    "source": ""  # Document name/section
}

# Plot Hook Schema - For quest/story extraction
PLOT_HOOK_SCHEMA = {
    "name": "",  # Quest or plot name
    "description": "",  # Full description
    "type": "",  # main/side/optional/random
    "npcs": [],  # Related NPCs by name
    "locations": [],  # Related locations
    "objectives": [],  # Quest objectives
    "rewards": "",  # Potential rewards
    "consequences": "",  # What happens if ignored/failed
    "level_range": "",  # Suggested character levels
    "source": ""  # Document name/section
}

# Monster Schema - For creature extraction
MONSTER_SCHEMA = {
    "name": "",  # Monster name
    "type": "",  # Monster type (beast/humanoid/undead/etc)
    "size": "",  # tiny/small/medium/large/huge/gargantuan
    "cr": "",  # Challenge rating
    "location": "",  # Where encountered
    "tactics": "",  # Combat tactics or behavior
    "treasure": [],  # Carried treasure
    "source": ""  # Document name/section
}

# Trap Schema - For trap/hazard extraction
TRAP_SCHEMA = {
    "name": "",  # Trap name
    "location": "",  # Where found
    "trigger": "",  # What triggers it
    "effect": "",  # What it does
    "detection_dc": None,  # DC to detect
    "disable_dc": None,  # DC to disable
    "damage": "",  # Damage dealt
    "source": ""  # Document name/section
}

# Faction Schema - For organization extraction
FACTION_SCHEMA = {
    "name": "",  # Faction name
    "description": "",  # Goals and nature
    "leader": "",  # Leader NPC name
    "members": [],  # Notable member NPCs
    "headquarters": "",  # Base location
    "allies": [],  # Allied factions
    "enemies": [],  # Enemy factions
    "source": ""  # Document name/section
}

# Batch extraction result schema
EXTRACTION_RESULT_SCHEMA = {
    "document": "",  # Source document name
    "extraction_date": "",  # When extracted
    "npcs": {},  # name -> NPC_SCHEMA
    "locations": {},  # name -> LOCATION_SCHEMA
    "items": {},  # name -> ITEM_SCHEMA
    "plot_hooks": {},  # name -> PLOT_HOOK_SCHEMA
    "monsters": {},  # name -> MONSTER_SCHEMA
    "traps": {},  # name -> TRAP_SCHEMA
    "factions": {},  # name -> FACTION_SCHEMA
    "metadata": {
        "total_chunks": 0,
        "chunks_processed": 0,
        "extraction_method": "concurrent_agents",
        "agents_used": []
    }
}

def get_schema(schema_type: str) -> dict:
    """Get a specific schema by type"""
    schemas = {
        'npc': NPC_SCHEMA,
        'location': LOCATION_SCHEMA,
        'item': ITEM_SCHEMA,
        'plot_hook': PLOT_HOOK_SCHEMA,
        'monster': MONSTER_SCHEMA,
        'trap': TRAP_SCHEMA,
        'faction': FACTION_SCHEMA,
        'result': EXTRACTION_RESULT_SCHEMA
    }
    return schemas.get(schema_type, {})


def validate_extraction(data: dict, schema_type: str) -> tuple[bool, list]:
    """
    Validate extracted data against schema
    Returns (is_valid, errors)
    """
    schema = get_schema(schema_type)
    errors = []

    if not schema:
        return False, [f"Unknown schema type: {schema_type}"]

    # Check required fields
    for field, default in schema.items():
        if field not in data and not isinstance(default, (list, dict)):
            errors.append(f"Missing required field: {field}")

    # Validate specific fields
    if schema_type == 'npc':
        if 'name' in data and len(data.get('name', '')) > 100:
            errors.append("NPC name exceeds 100 characters")
        if 'attitude' in data and data['attitude'] not in ['friendly', 'neutral', 'hostile', 'suspicious', 'helpful']:
            errors.append(f"Invalid attitude: {data['attitude']}")

    elif schema_type == 'item':
        valid_rarities = ['common', 'uncommon', 'rare', 'very rare', 'legendary', 'artifact']
        if 'rarity' in data and data['rarity'] and data['rarity'] not in valid_rarities:
            errors.append(f"Invalid rarity: {data['rarity']}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # Test schema validation
    test_npc = {
        "name": "Strahd von Zarovich",
        "description": "The vampire lord of Barovia, a tragic figure cursed to eternal undeath.",
        "attitude": "hostile",
        "location_tags": ["Castle Ravenloft"],
        "source": "Curse of Strahd"
    }

    valid, errors = validate_extraction(test_npc, 'npc')
    print(f"NPC validation: {'PASS' if valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")