"""D&D 5E formatting for session-context blocks.

Moved verbatim from lib/session_manager.get_full_context body. Both formatters
return strings that are appended directly into the context output by lib.
"""
from typing import Any, Dict


def _truncate(text: str, limit: int, full: bool) -> str:
    if full or not text or len(text) <= limit:
        return text
    return text[:limit - 3].rstrip() + "..."


def format_character_block(character: Dict[str, Any]) -> str:
    """Format the CHARACTER section of session context. Flat PC shape."""
    if not character:
        return "No character found."

    name = character.get('name', 'Unknown')
    level = character.get('level', 1)
    race = character.get('race', '?')
    cls = character.get('class', '?')
    hp = character.get('hp', {})
    hp_cur = hp.get('current', 0) if isinstance(hp, dict) else 0
    hp_max = hp.get('max', 0) if isinstance(hp, dict) else 0
    ac = character.get('ac', '?')
    xp = character.get('xp', {})
    if isinstance(xp, dict):
        xp_val = xp.get('current', 0)
    else:
        xp_val = xp
    gold = character.get('gold', 0)
    conditions = character.get('conditions', [])
    cond_str = ', '.join(conditions) if conditions else '(none)'

    lines = [
        f"{name} - Level {level} {race} {cls} | "
        f"HP: {hp_cur}/{hp_max} | AC: {ac} | XP: {xp_val} | Gold: {gold}",
        f"Conditions: {cond_str}",
    ]
    return "\n".join(lines)


def format_party_context_block(party: Dict[str, Dict], full: bool) -> str:
    """Format the PARTY MEMBERS section of session context. Wrapped NPC shape.

    Always returns a string ending with a newline so the caller can append it
    directly without adding an extra blank line separator.
    """
    if not party:
        return "(none)\n"

    party_items = list(party.items())
    max_party = len(party_items) if full else 8
    shown_party = party_items[:max_party]

    lines = []
    for npc_name, npc_data in shown_party:
        sheet = npc_data.get('character_sheet', {})
        hp = sheet.get('hp', {'current': 10, 'max': 10})
        ac = sheet.get('ac', 10)
        level = sheet.get('level', 1)
        race = sheet.get('race', 'Unknown')
        cls = sheet.get('class', 'Commoner')
        conditions = sheet.get('conditions', [])
        cond_str = f" [{', '.join(conditions)}]" if conditions else ""
        desc = _truncate(npc_data.get('description', ''), 180, full)

        lines.append(
            f"{npc_name} (Lvl {level} {race} {cls}) "
            f"HP: {hp['current']}/{hp['max']} AC: {ac}{cond_str}"
        )
        if desc:
            lines.append(f"  {desc}")

        events = npc_data.get('events', [])
        if events:
            recent = events[-3:] if full else events[-2:]
            event_strs = []
            for ev in recent:
                if isinstance(ev, dict):
                    event_strs.append(f"\"{_truncate(ev.get('event', ''), 120, full)}\"")
                else:
                    event_strs.append(f"\"{_truncate(str(ev), 120, full)}\"")
            lines.append(f"  Recent: {' -> '.join(event_strs)}")
        lines.append("")

    if not full and len(party_items) > max_party:
        lines.append(f"... and {len(party_items) - max_party} more party members (use --full)")
        lines.append("")

    return "\n".join(lines)
