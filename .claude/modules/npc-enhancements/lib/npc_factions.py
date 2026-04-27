#!/usr/bin/env python3
"""
NPC Faction tagging — group NPCs by faction for filtered views.

Stores faction membership in each NPC entry:
  {
    "Karvus": {
      ...
      "factions": ["Serpent Tongue", "Shahrazar Underworld"]
    }
  }
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set


def _get_npcs_path() -> Path:
    from campaign_manager import CampaignManager
    mgr = CampaignManager()
    return mgr.get_active_campaign_dir() / "npcs.json"


def _load_npcs() -> Dict:
    path = _get_npcs_path()
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (ValueError, IOError):
            return {}
    return {}


def _save_npcs(data: Dict) -> None:
    path = _get_npcs_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def tag_faction(name: str, *factions: str) -> Dict:
    """Add faction tags to an NPC."""
    npcs = _load_npcs()
    if name not in npcs:
        return {"error": f"NPC '{name}' not found"}

    if "factions" not in npcs[name]:
        npcs[name]["factions"] = []

    current = set(npcs[name]["factions"])
    added = []
    for f in factions:
        if f not in current:
            current.add(f)
            added.append(f)

    npcs[name]["factions"] = sorted(current)
    _save_npcs(npcs)
    return {"success": True, "name": name, "factions_added": added, "all_factions": npcs[name]["factions"]}


def untag_faction(name: str, *factions: str) -> Dict:
    """Remove faction tags from an NPC."""
    npcs = _load_npcs()
    if name not in npcs:
        return {"error": f"NPC '{name}' not found"}

    current = set(npcs[name].get("factions", []))
    removed = []
    for f in factions:
        if f in current:
            current.remove(f)
            removed.append(f)

    npcs[name]["factions"] = sorted(current)
    _save_npcs(npcs)
    return {"success": True, "name": name, "factions_removed": removed, "all_factions": npcs[name]["factions"]}


def list_factions() -> List[str]:
    """Return sorted list of all faction names across all NPCs."""
    npcs = _load_npcs()
    factions: Set[str] = set()
    for data in npcs.values():
        for f in data.get("factions", []):
            factions.add(f)
    return sorted(factions)


def get_faction_members(faction: str) -> List[Dict]:
    """List all NPCs in a given faction with their attitude."""
    npcs = _load_npcs()
    members = []
    for name, data in npcs.items():
        if faction in data.get("factions", []):
            members.append({
                "name": name,
                "attitude": data.get("attitude", "neutral"),
                "description": data.get("description", "")
            })
    return members


def format_factions_for_summary() -> str:
    """Generate a factions section for narrative-summary.md."""
    npcs = _load_npcs()
    if not npcs:
        return ""

    all_factions = list_factions()
    if not all_factions:
        return ""

    lines = ["## Factions"]
    for faction in all_factions:
        members = get_faction_members(faction)
        member_strs = [f"{m['name']} ({m['attitude']})" for m in members]
        lines.append(f"- **{faction}**: {', '.join(member_strs)}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: npc_factions.py <action> [args]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "tag" and len(sys.argv) >= 4:
        result = tag_faction(sys.argv[2], *sys.argv[3:])
        print(json.dumps(result, indent=2))

    elif action == "untag" and len(sys.argv) >= 4:
        result = untag_faction(sys.argv[2], *sys.argv[3:])
        print(json.dumps(result, indent=2))

    elif action == "list":
        factions = list_factions()
        if factions:
            print("Known factions:")
            for f in factions:
                print(f"  - {f}")
        else:
            print("No factions recorded yet.")

    elif action == "members" and len(sys.argv) == 3:
        members = get_faction_members(sys.argv[2])
        if members:
            print(f"Members of {sys.argv[2]}:")
            for m in members:
                print(f"  - {m['name']} ({m['attitude']}) — {m['description']}")
        else:
            print(f"No members found for faction '{sys.argv[2]}'")

    elif action == "summary":
        print(format_factions_for_summary())

    else:
        print("Usage:")
        print("  tag <name> <faction1> [faction2...]")
        print("  untag <name> <faction1> [faction2...]")
        print("  list")
        print("  members <faction>")
        print("  summary")
        sys.exit(1)
