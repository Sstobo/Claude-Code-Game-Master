#!/usr/bin/env python3
"""
JSON schemas and validation for DM world state files.
Provides schema definitions and validation functions for all entity types.
"""

from typing import Dict, Any, List, Tuple, Optional

# Valid attitudes for NPCs
VALID_ATTITUDES = {'ally', 'neutral', 'enemy', 'friendly', 'hostile', 'suspicious', 'helpful'}

# Valid plot types
VALID_PLOT_TYPES = {'main', 'side', 'personal', 'world', 'optional', 'scene', 'theme', 'idea', 'lore', 'background'}

# Valid plot statuses
VALID_PLOT_STATUSES = {'active', 'completed', 'failed', 'dormant', 'available'}

# Valid item types (broad categories - specific weapon/armor types allowed)
VALID_ITEM_TYPES = {
    'weapon', 'armor', 'potion', 'scroll', 'wondrous', 'treasure', 'equipment',
    'prop', 'artifact', 'misc', 'consumable', 'ring', 'amulet', 'tool', 'vehicle',
    'map', 'key', 'document', 'holy symbol', 'focus', 'container', 'clothing',
    # Specific weapon types (D&D)
    'sword', 'greatsword', 'longsword', 'shortsword', 'scimitar', 'rapier',
    'dagger', 'axe', 'greataxe', 'handaxe', 'mace', 'warhammer', 'maul',
    'spear', 'javelin', 'halberd', 'glaive', 'pike', 'trident', 'lance',
    'bow', 'longbow', 'shortbow', 'crossbow', 'heavy crossbow', 'light crossbow',
    'staff', 'quarterstaff', 'club', 'greatclub', 'flail', 'morningstar', 'whip',
    # Specific armor types
    'light armor', 'medium armor', 'heavy armor', 'shield',
    # Fantasy types
    'treasure hoard', 'ring (artifact)', 'various'
}

# Valid item rarities
VALID_RARITIES = {'common', 'uncommon', 'rare', 'very rare', 'legendary', 'artifact'}


def validate_npc(name: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate NPC data against schema.

    Args:
        name: NPC name (key)
        data: NPC data dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not data.get('description'):
        errors.append(f"NPC '{name}': missing description")

    attitude = data.get('attitude', '').lower()
    if not attitude:
        errors.append(f"NPC '{name}': missing attitude")
    elif attitude not in VALID_ATTITUDES:
        errors.append(f"NPC '{name}': invalid attitude '{attitude}' (valid: {', '.join(VALID_ATTITUDES)})")

    # Validate events array
    events = data.get('events', [])
    if not isinstance(events, list):
        errors.append(f"NPC '{name}': events must be a list")

    # Validate tags structure
    tags = data.get('tags', {})
    if isinstance(tags, dict):
        if 'locations' in tags and not isinstance(tags['locations'], list):
            errors.append(f"NPC '{name}': tags.locations must be a list")
        if 'quests' in tags and not isinstance(tags['quests'], list):
            errors.append(f"NPC '{name}': tags.quests must be a list")
    elif isinstance(tags, list):
        # Legacy format - just a list of tags, which is fine
        pass
    else:
        errors.append(f"NPC '{name}': tags must be a dict or list")

    # Validate character sheet if party member (opaque dict — ruleset interprets shape)
    if data.get('is_party_member') and 'character_sheet' in data:
        if not isinstance(data['character_sheet'], dict):
            errors.append(f"NPC '{name}': character_sheet must be a dict")

    return len(errors) == 0, errors


def validate_location(name: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate location data against schema.

    Args:
        name: Location name (key)
        data: Location data dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not data.get('description') and not data.get('name'):
        errors.append(f"Location '{name}': missing description")

    # Validate connections
    connections = data.get('connections', [])
    if not isinstance(connections, list):
        errors.append(f"Location '{name}': connections must be a list")

    # Validate npcs list
    npcs = data.get('npcs', [])
    if not isinstance(npcs, list):
        errors.append(f"Location '{name}': npcs must be a list")

    # Validate tags
    tags = data.get('tags', [])
    if not isinstance(tags, list):
        errors.append(f"Location '{name}': tags must be a list")

    # Dungeon room validation
    if data.get('dungeon'):
        exits = data.get('exits', {})
        if not isinstance(exits, dict):
            errors.append(f"Location '{name}': dungeon room exits must be a dict")

    return len(errors) == 0, errors


def validate_plot(name: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate plot/quest data against schema.

    Args:
        name: Plot name (key)
        data: Plot data dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not data.get('description') and not data.get('name'):
        errors.append(f"Plot '{name}': missing description")

    # Validate type if present
    plot_type = data.get('type', '').lower()
    if plot_type and plot_type not in VALID_PLOT_TYPES:
        errors.append(f"Plot '{name}': invalid type '{plot_type}' (valid: {', '.join(VALID_PLOT_TYPES)})")

    # Validate status if present
    status = data.get('status', '').lower()
    if status and status not in VALID_PLOT_STATUSES:
        errors.append(f"Plot '{name}': invalid status '{status}' (valid: {', '.join(VALID_PLOT_STATUSES)})")

    # Validate lists
    for field in ['npcs', 'locations', 'objectives', 'progress']:
        if field in data and not isinstance(data[field], list):
            errors.append(f"Plot '{name}': {field} must be a list")

    return len(errors) == 0, errors


def validate_item(name: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate item data against schema.

    Args:
        name: Item name (key)
        data: Item data dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not data.get('description') and not data.get('name'):
        errors.append(f"Item '{name}': missing description")

    # Validate type if present
    item_type = data.get('type', '').lower()
    if item_type and item_type not in VALID_ITEM_TYPES:
        errors.append(f"Item '{name}': invalid type '{item_type}' (valid: {', '.join(VALID_ITEM_TYPES)})")

    # Validate rarity if present
    rarity = data.get('rarity', '').lower()
    if rarity and rarity not in VALID_RARITIES:
        errors.append(f"Item '{name}': invalid rarity '{rarity}' (valid: {', '.join(VALID_RARITIES)})")

    return len(errors) == 0, errors


def validate_consequence(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate consequence data against schema.

    Args:
        data: Consequence data dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not data.get('id'):
        errors.append("Consequence: missing id")
    if not data.get('consequence'):
        errors.append("Consequence: missing consequence description")
    if not data.get('trigger'):
        errors.append("Consequence: missing trigger condition")

    return len(errors) == 0, errors


def validate_campaign_overview(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate campaign overview data against schema.

    Args:
        data: Campaign overview dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not data.get('campaign_name'):
        errors.append("Campaign: missing campaign_name")

    # Validate player_position structure
    pos = data.get('player_position', {})
    if not isinstance(pos, dict):
        errors.append("Campaign: player_position must be a dict")

    # Validate tone structure
    tone = data.get('tone', {})
    if isinstance(tone, dict):
        for key in ['horror', 'comedy', 'drama']:
            if key in tone and not isinstance(tone[key], (int, float)):
                errors.append(f"Campaign: tone.{key} must be a number")

    return len(errors) == 0, errors


def validate_character(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate player character data — system-agnostic top-level checks only.

    Sheet-shaped fields (hp, ac, abilities, etc.) are opaque to lib. The active
    ruleset re-validates them on action paths.
    """
    errors = []

    required = ['name', 'race', 'class', 'level']
    for field in required:
        if not data.get(field):
            errors.append(f"Character: missing {field}")

    return len(errors) == 0, errors


def validate_world_state(campaign_dir: str) -> Dict[str, List[str]]:
    """Validate all world state files in a campaign directory.

    Args:
        campaign_dir: Path to campaign directory

    Returns:
        Dict mapping filename to list of errors (empty list if valid)
    """
    import json
    from pathlib import Path

    results = {}
    campaign_path = Path(campaign_dir)

    # Validate each file type
    validators = {
        'npcs.json': ('npcs', validate_npc),
        'locations.json': ('locations', validate_location),
        'plots.json': ('plots', validate_plot),
        'items.json': ('items', validate_item),
        'campaign-overview.json': (None, validate_campaign_overview),
        'character.json': (None, validate_character),
    }

    for filename, (entity_key, validator) in validators.items():
        filepath = campaign_path / filename
        if not filepath.exists():
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            results[filename] = [f"Invalid JSON: {e}"]
            continue
        except IOError as e:
            results[filename] = [f"Read error: {e}"]
            continue

        errors = []

        if entity_key is None:
            # Single object validation
            valid, errs = validator(data)
            errors.extend(errs)
        else:
            # Dict of entities validation
            if isinstance(data, dict):
                # Handle both {name: data} and {key: {name: data}} formats
                entities = data.get(entity_key, data)
                if isinstance(entities, dict):
                    for name, entity_data in entities.items():
                        if isinstance(entity_data, dict):
                            valid, errs = validator(name, entity_data)
                            errors.extend(errs)

        results[filename] = errors

    # Validate consequences separately (different structure)
    consequences_file = campaign_path / 'consequences.json'
    if consequences_file.exists():
        try:
            with open(consequences_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            errors = []
            for consequence in data.get('active', []) + data.get('resolved', []):
                valid, errs = validate_consequence(consequence)
                errors.extend(errs)
            results['consequences.json'] = errors
        except (json.JSONDecodeError, IOError) as e:
            results['consequences.json'] = [str(e)]

    return results


def main():
    """CLI interface for schema validation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Validate world state schemas')
    parser.add_argument('campaign_dir', nargs='?', help='Campaign directory to validate')
    parser.add_argument('--all', action='store_true', help='Validate all campaigns')

    args = parser.parse_args()

    from pathlib import Path

    if args.all:
        campaigns_dir = Path('world-state/campaigns')
        if not campaigns_dir.exists():
            print("No campaigns directory found")
            sys.exit(1)

        all_valid = True
        for campaign_path in campaigns_dir.iterdir():
            if campaign_path.is_dir():
                print(f"\n=== {campaign_path.name} ===")
                results = validate_world_state(str(campaign_path))
                for filename, errors in results.items():
                    if errors:
                        all_valid = False
                        print(f"  {filename}: {len(errors)} errors")
                        for err in errors[:3]:  # Show first 3 errors
                            print(f"    - {err}")
                        if len(errors) > 3:
                            print(f"    ... and {len(errors) - 3} more")
                    else:
                        print(f"  {filename}: OK")

        sys.exit(0 if all_valid else 1)

    elif args.campaign_dir:
        results = validate_world_state(args.campaign_dir)
        all_valid = True
        for filename, errors in results.items():
            if errors:
                all_valid = False
                print(f"{filename}: {len(errors)} errors")
                for err in errors:
                    print(f"  - {err}")
            else:
                print(f"{filename}: OK")

        sys.exit(0 if all_valid else 1)

    else:
        # Try to validate active campaign
        try:
            from campaign_manager import CampaignManager
            mgr = CampaignManager()
            campaign_dir = mgr.get_active_campaign_dir()
            if campaign_dir:
                print(f"Validating active campaign: {campaign_dir.name}")
                results = validate_world_state(str(campaign_dir))
                all_valid = True
                for filename, errors in results.items():
                    if errors:
                        all_valid = False
                        print(f"  {filename}: {len(errors)} errors")
                        for err in errors:
                            print(f"    - {err}")
                    else:
                        print(f"  {filename}: OK")
                sys.exit(0 if all_valid else 1)
            else:
                print("No active campaign")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
