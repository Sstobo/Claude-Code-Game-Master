#!/usr/bin/env python3
"""
NPC Relationship tracking — bidirectional relationship management.

Stores relationships in npcs.json as a dict keyed by NPC name:
  {
    "Karvus": {
      ...
      "relationships": {
        "Grom": {"type": "ally", "notes": "Business partners in the Serpent Tongue deal"}
      }
    }
  }

Relationships are always saved to BOTH sides with proper inverse mapping.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, List

VALID_RELATIONSHIP_TYPES = [
    "ally", "enemy", "contact", "rival", "family",
    "mentor", "protege", "subordinate", "superior", "acquaintance"
]

# Symmetric: ally↔ally, enemy↔enemy, rival↔rival, etc.
# Asymmetric: mentor↔protege, superior↔subordinate
_INVERSE_MAP = {
    "ally": "ally",
    "enemy": "enemy",
    "contact": "contact",
    "rival": "rival",
    "family": "family",
    "acquaintance": "acquaintance",
    "mentor": "protege",
    "protege": "mentor",
    "superior": "subordinate",
    "subordinate": "superior",
}


def inverse_type(rel_type: str) -> str:
    """Return the inverse relationship type for bidirectional storage."""
    return _INVERSE_MAP.get(rel_type, rel_type)


def _get_npcs_path() -> Path:
    """Resolve npcs.json relative to the active campaign."""
    from campaign_manager import CampaignManager
    mgr = CampaignManager()
    return mgr.get_active_campaign_dir() / "npcs.json"


def _load_npcs() -> Dict:
    """Load npcs.json, return empty dict if missing."""
    path = _get_npcs_path()
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (ValueError, IOError):
            return {}
    return {}


def _save_npcs(data: Dict) -> None:
    """Save npcs.json atomically."""
    path = _get_npcs_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_relationship(npc_a: str, npc_b: str, rel_type: str, notes: str = "") -> Dict:
    """
    Set a bidirectional relationship between two NPCs.
    Writes to BOTH sides with proper inverse mapping.
    Returns the updated npcs.json data.
    """
    if rel_type not in VALID_RELATIONSHIP_TYPES:
        valid = ", ".join(VALID_RELATIONSHIP_TYPES)
        return {"error": f"Invalid relationship type '{rel_type}'. Valid: {valid}"}

    npcs = _load_npcs()

    # Ensure both NPCs exist
    for name in [npc_a, npc_b]:
        if name not in npcs:
            return {"error": f"NPC '{name}' not found. Create them first with dm-npc.sh create"}

    # Initialize relationships dict if missing
    for name in [npc_a, npc_b]:
        if "relationships" not in npcs[name]:
            npcs[name]["relationships"] = {}

    # Set A → B
    npcs[npc_a]["relationships"][npc_b] = {
        "type": rel_type,
        "notes": notes
    }

    # Set B → A (inverse)
    inv = inverse_type(rel_type)
    inverse_notes = notes
    if inv != rel_type:
        inverse_notes = f"{notes} (inverse: {inv})" if notes else f"(inverse relationship: {inv})"

    npcs[npc_b]["relationships"][npc_a] = {
        "type": inv,
        "notes": inverse_notes
    }

    _save_npcs(npcs)
    return {
        "success": True,
        "relationship": f"{npc_a} ↔ {npc_b}: {rel_type}/{inv}",
        "notes": notes
    }


def remove_relationship(npc_a: str, npc_b: str) -> Dict:
    """Remove a bidirectional relationship between two NPCs."""
    npcs = _load_npcs()

    for name in [npc_a, npc_b]:
        if name in npcs and "relationships" in npcs[name]:
            npcs[name]["relationships"].pop(npc_b, None)

    _save_npcs(npcs)
    return {"success": True, "removed": f"{npc_a} ↔ {npc_b}"}


def get_relationships(name: str) -> Dict:
    """Get all relationships for an NPC."""
    npcs = _load_npcs()
    if name not in npcs:
        return {"error": f"NPC '{name}' not found"}
    return npcs[name].get("relationships", {})


def format_relationships(name: str) -> str:
    """Pretty-print relationships for terminal display."""
    npcs = _load_npcs()
    if name not in npcs:
        return f"NPC '{name}' not found"

    rels = npcs[name].get("relationships", {})
    if not rels:
        return f"{name} has no recorded relationships."

    lines = [f"Relationships for {name}:"]
    for other_name, rel_data in rels.items():
        rel_type = rel_data.get("type", "unknown")
        notes = rel_data.get("notes", "")
        notes_str = f" — {notes}" if notes else ""
        other_attitude = npcs.get(other_name, {}).get("attitude", "?")
        lines.append(f"  {other_name} ({other_attitude}): {rel_type}{notes_str}")
    return "\n".join(lines)


def format_for_summary() -> str:
    """Generate a relationships section for narrative-summary.md."""
    npcs = _load_npcs()
    if not npcs:
        return ""

    sections = []
    for name, data in npcs.items():
        rels = data.get("relationships", {})
        if rels:
            rel_strs = []
            for other, rdata in rels.items():
                t = rdata.get("type", "?")
                n = rdata.get("notes", "")
                ns = f" ({n})" if n else ""
                rel_strs.append(f"{t} of {other}{ns}")
            sections.append(f"- **{name}**: {', '.join(rel_strs)}")

    if not sections:
        return ""

    return "## NPC Relationships\n" + "\n".join(sections) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: npc_relationships.py <action> [args]")
        print("Actions: set, remove, get, format")
        sys.exit(1)

    action = sys.argv[1]

    if action == "set" and len(sys.argv) >= 5:
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        result = set_relationship(sys.argv[2], sys.argv[3], notes)
        print(json.dumps(result, indent=2))

    elif action == "remove" and len(sys.argv) == 4:
        result = remove_relationship(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2))

    elif action == "get" and len(sys.argv) == 3:
        result = get_relationships(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif action == "format" and len(sys.argv) == 3:
        print(format_relationships(sys.argv[2]))

    elif action == "summary":
        print(format_for_summary())

    else:
        print("Usage:")
        print("  set <npc_a> <npc_b> <type> [notes]")
        print("  remove <npc_a> <npc_b>")
        print("  get <name>")
        print("  format <name>")
        print("  summary")
        sys.exit(1)
