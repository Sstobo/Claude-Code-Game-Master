#!/usr/bin/env python3
"""
Auto-prompt on first NPC encounter.

After session end/save, checks if the session log contains NPC names
not yet in npcs.json and prompts the DM to save them.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional


def _get_campaign_dir() -> Path:
    from campaign_manager import CampaignManager
    mgr = CampaignManager()
    return mgr.get_active_campaign_dir()


def _get_npcs_path() -> Path:
    return _get_campaign_dir() / "npcs.json"


def _get_session_number() -> int:
    """Get current session number from session-log.md."""
    log_path = _get_campaign_dir() / "session-log.md"
    if not log_path.exists():
        return 0
    content = log_path.read_text(encoding='utf-8')
    return content.count("Session Started:")


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


def save_npc(name: str, description: str = "", attitude: str = "neutral", location: str = "") -> Dict:
    """
    Save a new NPC to npcs.json with first_encounter tracking.

    Returns result dict with success/error.
    """
    npcs = _load_npcs()

    if name in npcs:
        return {"error": f"NPC '{name}' already exists", "existing": True}

    from datetime import datetime, timezone

    npcs[name] = {
        "description": description or "(auto-extracted)",
        "attitude": attitude,
        "created": datetime.now(timezone.utc).isoformat(),
        "events": [],
        "tags": {"locations": [], "quests": []},
        "relationships": {},
        "factions": [],
        "attitude_history": [{"attitude": attitude, "timestamp": datetime.now(timezone.utc).isoformat()}],
        "first_encounter": {
            "session": _get_session_number(),
            "location": location or "unknown",
            "summary": f"Auto-detected from session narrative"
        }
    }

    _save_npcs(npcs)
    return {"success": True, "name": name, "created": True}


def prompt_and_save(candidates: List[Dict], location: str = "", auto_approve: bool = False) -> List[str]:
    """
    Prompt the DM to save each candidate NPC.

    In auto-approve mode (DM_AUTO_APPROVE=1 or testing), skips prompts.
    Returns list of saved NPC names.
    """
    saved = []
    auto = auto_approve or os.environ.get("DM_AUTO_APPROVE") == "1"

    for candidate in candidates:
        name = candidate["name"]
        confidence = candidate["confidence"]
        count = candidate["count"]

        # Skip low-confidence in auto mode
        if confidence == "low" and not auto:
            continue

        if auto:
            desc = f"(auto-extracted, appears {count}x, confidence: {confidence})"
            result = save_npc(name, description=desc, location=location)
            if result.get("success"):
                saved.append(name)
            continue

        # Interactive prompt
        print(f"\n[NEW NPC] '{name}' (appears {count}x, confidence: {confidence})")
        print(f"  Save this NPC? (y/n, or 'describe: <text>' to save with description)")

        try:
            response = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if response.lower() == "y":
            result = save_npc(name, location=location)
            if result.get("success"):
                print(f"  ✓ Saved '{name}' to npcs.json")
                saved.append(name)
        elif response.lower().startswith("describe:"):
            desc = response[9:].strip()
            result = save_npc(name, description=desc, location=location)
            if result.get("success"):
                print(f"  ✓ Saved '{name}' with description")
                saved.append(name)
        else:
            print(f"  Skipped '{name}'")

    return saved


if __name__ == "__main__":
    import json
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        from npc_extractor import extract_from_session_log
        candidates = extract_from_session_log()
        saved = prompt_and_save(candidates, auto_approve=True)
        print(json.dumps({"saved": saved, "skipped": len([c for c in candidates if c["name"] not in saved])}))
    else:
        print("Usage: npc_autoprompt.py --auto")
        print("       (or import and use programmatically)")
        sys.exit(1)
