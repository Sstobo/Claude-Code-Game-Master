#!/usr/bin/env python3
"""
Identity-first onboarding — "Who are you in this world?"

Replaces the mandatory 9-step 5e builder with one question. The player picks:
  - canon:    play a character from the book (lift stats/voice from npcs.json)
  - original: a name + one-line concept (mechanics inferred silently by the kit)
  - nameless: a nameless traveler (zero required mechanics)

All three produce an open-schema character (see character_schema). The full
builder stays available as an opt-in. Mechanics are inferred + persisted
invisibly; the player spends the "I love this book" spike on story, not setup.
"""

import copy
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager


def _default_vitals() -> Dict[str, Any]:
    """Fresh nested vitals every call (avoid shared-dict aliasing across characters)."""
    return {"hp": {"current": 10, "max": 10}, "ac": 10}


class IdentityOnboarding(EntityManager):
    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)

    def from_canon(self, npc_name: str) -> Optional[Dict[str, Any]]:
        """Lift a canon character from npcs.json (stats from a sheet if present, voice from context)."""
        npcs = self.json_ops.load_json("npcs.json") or {}
        npc = npcs.get(npc_name)
        if not isinstance(npc, dict):
            return None
        sheet = npc.get("character_sheet") or {}
        return {
            "identity": {"name": npc_name, "race": sheet.get("race", ""), "class": sheet.get("class", "")},
            "vitals": {"hp": copy.deepcopy(sheet.get("hp", _default_vitals()["hp"])), "ac": sheet.get("ac", 10)},
            "attributes": dict(sheet.get("stats", {})),
            "progression": {"level": sheet.get("level", 1)},
            "inventory": {"gold": 0, "items": list(sheet.get("equipment", []))},
            "conditions": list(sheet.get("conditions", [])),
            "voice": npc.get("context", []),
            "origin": "canon",
        }

    def original(self, name: str, concept: str = "") -> Dict[str, Any]:
        return {
            "identity": {"name": name, "concept": concept},
            "vitals": _default_vitals(),
            "attributes": {},  # inferred silently against the active kit
            "progression": {"level": 1},
            "inventory": {"gold": 0, "items": []},
            "conditions": [],
            "origin": "original",
        }

    def nameless(self) -> Dict[str, Any]:
        return {
            "identity": {"name": "A nameless traveler"},
            "vitals": _default_vitals(),
            "attributes": {},
            "progression": {"level": 1},
            "inventory": {"gold": 0, "items": []},
            "conditions": [],
            "origin": "nameless",
        }

    def build(self, mode: str, **kw) -> Optional[Dict[str, Any]]:
        if mode == "canon":
            return self.from_canon(kw.get("npc_name", ""))
        if mode == "original":
            return self.original(kw.get("name", "Traveler"), kw.get("concept", ""))
        return self.nameless()

    def save_character(self, char: Dict[str, Any]) -> bool:
        """Persist the chosen identity as the campaign character (open schema)."""
        return self.json_ops.save_json("character.json", char)
