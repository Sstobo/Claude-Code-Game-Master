#!/usr/bin/env python3
"""
World Kit: the per-campaign ruleset that sits on top of the generic game core.

A campaign's `ruleset.json` declares HOW that world plays — its stat schema, its
progression model, its resolution model, and which specialist agents are active —
without baking D&D 5e into the engine. The WorldKit loads it and drives play
through `game_core`, so a Dune kit and a Dungeon Crawler Carl kit run the same
core with entirely different rules. World-flavor systems (loot boxes, viewers,
etc.) stay in campaign-overview's `campaign_rules` and are surfaced alongside.

ruleset.json shape:
{
  "name": "Dungeon Crawler Carl",
  "stat_schema": { "attributes": ["str","con","dex","int"], "vitals": ["hp"] },
  "progression": { "model": "resource-axis", "resource": "viewers",
                   "tiers": [1000000, 1000000000] },
  "resolution": { "model": "d20-vs-dc" },
  "active_agents": ["monster-manual", "loot-dropper"],
  "rules_doc": "rules.md"        # optional: campaign-scoped rules prose, loaded on demand
}
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from campaign_manager import CampaignManager
from game_core import make_progression, opposed_check, resolve_check


DEFAULT_RULESET = {
    "name": "Generic Adventure",
    "kit": "custom",
    "stat_schema": {"attributes": [], "vitals": ["hp"]},
    "progression": {"model": "milestone"},
    "resolution": {"model": "d20-vs-dc"},
    "active_agents": [],
    "rules_doc": None,
}


class WorldKit:
    """Loads a campaign's ruleset.json and drives play through the generic core."""

    def __init__(self, world_state_dir: str = None):
        base = world_state_dir or "world-state"
        cm = CampaignManager(base)
        self.campaign_dir = cm.get_active_campaign_dir()
        self.json_ops = JsonOperations(str(self.campaign_dir))
        self.ruleset = self.json_ops.load_json("ruleset.json") or dict(DEFAULT_RULESET)
        prog = self.ruleset.get("progression", {}) or {}
        if isinstance(prog, str):          # shorthand: "progression": "milestone"
            prog = {"model": prog}
        self.progression = make_progression(
            prog.get("model", "milestone"),
            **{k: v for k, v in prog.items() if k != "model"},
        )

    # --- declared configuration ---
    def name(self) -> str:
        return self.ruleset.get("name", "Generic Adventure")

    def kit(self) -> str:
        """Kit identity: 'dnd5e' unlocks the D&D mechanics skills + dnd5eapi.

        Anything else (default 'custom') runs the generic core + this ruleset.
        Legacy rulesets without the field are 'custom' — the safe reading, since
        loading 5e mechanics into a bespoke world is the failure this prevents.
        """
        return self.ruleset.get("kit", "custom")

    def stat_schema(self) -> Dict[str, Any]:
        return self.ruleset.get("stat_schema", {})

    def vitals(self) -> List[str]:
        """Vital tracks this world declares ('hp' plus kit vitals: vigor,
        corruption, water, ...).

        A kit that declares none — no `stat_schema`, an empty list, or no ruleset at
        all — gets ['hp']. Every world has a body; returning nothing here would make
        an under-declared kit refuse plain damage.
        """
        return (self.stat_schema() or {}).get("vitals") or ["hp"]

    def resolution(self) -> Dict[str, Any]:
        """{'model': name, 'params': {...}} regardless of ruleset syntax.

        A kit may declare `"resolution": "dice-pool"` or the fuller
        `{"model": "dice-pool", "target": 5}`; game_core.resolve_check gets the
        same clean shape either way.
        """
        raw = self.ruleset.get("resolution") or {}
        if isinstance(raw, str):
            return {"model": raw, "params": {}}
        params = {k: v for k, v in raw.items() if k != "model"}
        params.update(params.pop("params", {}) or {})
        return {"model": raw.get("model") or "d20-vs-dc", "params": params}

    def resolution_model(self) -> str:
        return self.resolution()["model"]

    def progression_model(self) -> str:
        prog = self.ruleset.get("progression") or {}
        if isinstance(prog, str):
            return prog
        return prog.get("model", "milestone")

    def active_agents(self) -> List[str]:
        return self.ruleset.get("active_agents", [])

    def rules_doc_path(self) -> Optional[Path]:
        """Path to the campaign's rules prose (loaded on demand), if declared + present."""
        doc = self.ruleset.get("rules_doc")
        if not doc:
            return None
        p = self.campaign_dir / doc
        return p if p.exists() else None

    def campaign_rules(self) -> Dict[str, Any]:
        """World-flavor systems (loot boxes, viewers, ...) from campaign-overview."""
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        return overview.get("campaign_rules", {})

    # --- play, driven through the generic core ---
    def resolve(self, modifier: int = 0, dc: int = 10, advantage: str = None) -> Dict[str, Any]:
        """Roll under THIS world's resolution model (d20, 2d6, dice pool, ...)."""
        return resolve_check(modifier, dc, advantage, model=self.resolution())

    def oppose(self, modifier_a: int = 0, modifier_b: int = 0,
               advantage_a: str = None, advantage_b: str = None) -> Dict[str, Any]:
        """Contest two sides under THIS world's resolution model."""
        return opposed_check(modifier_a, modifier_b, advantage_a, advantage_b,
                             model=self.resolution())

    def advance_progression(self, state: Dict[str, Any], **kw) -> Dict[str, Any]:
        return self.progression.advance(state, **kw)

    def level(self, state: Dict[str, Any]) -> int:
        return self.progression.level(state)


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit

    parser = argparse.ArgumentParser(description="World Kit info")
    parser.add_argument("action", nargs="?", default="info", choices=["info"])
    json_mode = wants_json()
    parser.parse_args(strip_json_flag(sys.argv[1:]))

    kit = WorldKit()
    info = {
        "name": kit.name(),
        "kit": kit.kit(),
        "stat_schema": kit.stat_schema(),
        "resolution_model": kit.resolution_model(),
        "progression_model": kit.progression_model(),
        "active_agents": kit.active_agents(),
        "rules_doc": str(kit.rules_doc_path()) if kit.rules_doc_path() else None,
    }
    if json_mode:
        emit(info, json_mode=True)
    else:
        print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
