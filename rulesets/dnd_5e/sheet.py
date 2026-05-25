"""D&D 5E character sheet logic.

Moved verbatim from lib/npc_manager.py: PARTY_MEMBER_DEFAULTS, sheet seed,
HP-as-{current,max} update bounds, field-name semantics, formatters.
"""
import copy
from typing import Any, Dict, Optional


PARTY_MEMBER_DEFAULTS = {
    "race": "Unknown",
    "class": "Commoner",
    "level": 1,
    "hp": {"current": 10, "max": 10},
    "ac": 10,
    "stats": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
    "saves": {"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0},
    "skills": {},
    "attack_bonus": 2,
    "damage": "1d6",
    "equipment": [],
    "features": [],
    "conditions": [],
    "xp": 0,
}


def init_sheet(npc_data: Dict[str, Any]) -> None:
    """Seed character_sheet on a freshly promoted party member."""
    npc_data['character_sheet'] = copy.deepcopy(PARTY_MEMBER_DEFAULTS)


def update_hp(sheet: Dict[str, Any], delta: int) -> Dict[str, Any]:
    hp = sheet.get('hp', {'current': 10, 'max': 10})
    old_current = hp['current']
    max_hp = hp['max']
    new_current = max(0, min(max_hp, old_current + delta))
    hp['current'] = new_current
    sheet['hp'] = hp
    if new_current == 0:
        status: Optional[str] = 'UNCONSCIOUS'
    elif new_current <= max_hp // 4:
        status = 'BLOODIED'
    else:
        status = None
    return {'old': old_current, 'new': new_current, 'max': max_hp, 'status': status}


def update_xp(sheet: Dict[str, Any], delta: int) -> Dict[str, Any]:
    sheet['xp'] = max(0, sheet.get('xp', 0) + delta)
    return sheet


def _parse_int(val: Any, field_name: str) -> Optional[int]:
    try:
        return int(str(val).strip())
    except ValueError:
        print(f"[ERROR] Invalid integer value for {field_name}: '{val}'")
        return None


def set_field(sheet: Dict[str, Any], field: str, value: Any) -> bool:
    """Set a sheet field. Returns False on unknown field or bad value."""
    if field == 'hp_max':
        parsed = _parse_int(value, 'hp_max')
        if parsed is None:
            return False
        if 'hp' not in sheet:
            sheet['hp'] = {'current': parsed, 'max': parsed}
        else:
            sheet['hp']['max'] = parsed
            if sheet['hp']['current'] > sheet['hp']['max']:
                sheet['hp']['current'] = sheet['hp']['max']
        return True
    if field == 'attack':
        parsed = _parse_int(value, 'attack')
        if parsed is None:
            return False
        sheet['attack_bonus'] = parsed
        return True
    if field in ('ac', 'level', 'xp'):
        parsed = _parse_int(value, field)
        if parsed is None:
            return False
        sheet[field] = max(0, parsed) if field == 'xp' else parsed
        return True
    if field in ('class', 'race', 'damage'):
        sheet[field] = str(value)
        return True
    print(f"[ERROR] Unknown field: {field}")
    print("Valid fields: ac, level, class, race, attack, damage, hp_max")
    return False


def format_npc_sheet(npc_data: Dict[str, Any]) -> Optional[str]:
    """Return the PARTY MEMBER block for an NPC's status display."""
    sheet = npc_data.get('character_sheet', {})
    lines = ["--- PARTY MEMBER ---"]

    hp = sheet.get('hp', {'current': 10, 'max': 10})
    lines.append(f"HP: {hp['current']}/{hp['max']} | AC: {sheet.get('ac', 10)}")
    lines.append(
        f"Level {sheet.get('level', 1)} {sheet.get('race', 'Unknown')} "
        f"{sheet.get('class', 'Commoner')}"
    )
    lines.append(
        f"Attack: +{sheet.get('attack_bonus', 2)} | Damage: {sheet.get('damage', '1d6')}"
    )
    lines.append(f"XP: {sheet.get('xp', 0)}")

    stats = sheet.get('stats', {})
    if stats:
        stat_line = " | ".join([f"{k.upper()}: {v}" for k, v in stats.items()])
        lines.append(f"Stats: {stat_line}")

    equipment = sheet.get('equipment', [])
    lines.append(f"Equipment: {', '.join(equipment) if equipment else 'None'}")

    features = sheet.get('features', [])
    if features:
        lines.append(f"Features: {', '.join(features)}")

    conditions = sheet.get('conditions', [])
    if conditions:
        lines.append(f"Conditions: {', '.join(conditions)}")

    return "\n".join(lines)


def format_party_summary(party: Dict[str, Dict]) -> str:
    """Return the `dm-npc.sh party` summary."""
    if not party:
        return "No party members. Use 'dm-npc.sh promote \"Name\"' to add NPCs to the party."

    lines = ["=== PARTY MEMBERS ===", ""]
    for name, data in party.items():
        sheet = data.get('character_sheet', {})
        hp = sheet.get('hp', {'current': 10, 'max': 10})
        ac = sheet.get('ac', 10)
        level = sheet.get('level', 1)
        char_class = sheet.get('class', 'Commoner')
        conditions = sheet.get('conditions', [])

        status = f"{name} - Lvl {level} {char_class}"
        hp_str = f"HP: {hp['current']}/{hp['max']}"
        ac_str = f"AC: {ac}"

        if hp['current'] == 0:
            hp_str += " [DOWN!]"
        elif hp['current'] <= hp['max'] // 4:
            hp_str += " [CRITICAL]"

        cond_str = f" [{', '.join(conditions)}]" if conditions else ""

        lines.append(f"  {status}")
        lines.append(f"    {hp_str} | {ac_str}{cond_str}")
        lines.append("")

    return "\n".join(lines)


def format_character_summary(char: Dict[str, Any]) -> str:
    """One-liner for CLI display: name, race, class, level, HP, gold."""
    hp = char.get('hp', {})
    gold = char.get('gold', 0)
    summary = (
        f"{char.get('name', 'Unknown')} - "
        f"{char.get('race', '?')} {char.get('class', '?')} "
        f"Level {char.get('level', 1)} "
        f"(HP: {hp.get('current', 0)}/{hp.get('max', 0)}, Gold: {gold})"
    )
    conditions = char.get('conditions', [])
    if conditions:
        summary += f" | Conditions: {', '.join(conditions)}"
    return summary
