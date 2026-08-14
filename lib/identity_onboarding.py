#!/usr/bin/env python3
"""
Identity-first onboarding — "Who are you in this world?"

Replaces the mandatory 9-step 5e builder with one question. The player picks:
  - canon:    play a character from the book (lift stats/voice from npcs.json)
  - original: a name + one-line concept (mechanics inferred silently by the kit)
  - nameless: a nameless traveler (zero required mechanics)

All three build a character internally in the structured (open) shape, then
persist it in the canonical FLAT shape via to_flat (see character_schema). The
full builder stays available as an opt-in. Mechanics are inferred + persisted
invisibly; the player spends the "I love this book" spike on story, not setup.
"""

import copy
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
from character_schema import to_flat


def _default_vitals() -> Dict[str, Any]:
    """Fresh nested vitals every call (avoid shared-dict aliasing across characters)."""
    return {"hp": {"current": 10, "max": 10}, "ac": 10}


class IdentityOnboarding(EntityManager):
    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)

    def from_canon(self, npc_name: str) -> Optional[Dict[str, Any]]:
        """Lift a canon character from npcs.json (stats from a sheet if present, voice from context).

        The name is resolved alias-aware (like become()), so "mordecai" or a title
        variant finds the canonical key — and that key becomes the PC's name."""
        resolved = self._find_entity_name("npcs.json", npc_name)
        if not resolved:
            return None
        npc_name = resolved
        npcs = self.json_ops.load_json("npcs.json") or {}
        npc = npcs.get(npc_name)
        if not isinstance(npc, dict):
            return None
        sheet = npc.get("character_sheet") or {}
        return {
            # Only these fields are lifted, so a death stamp on the NPC's sheet
            # (died_at / cause) can never ride along into the new PC.
            "status": "alive",
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
        """Persist the chosen identity as the campaign character (canonical flat).

        The builder works in the structured open shape; to_flat converts it to the
        canonical flat shape the runtime reads (and preserves extras like voice/
        origin/concept at the top level)."""
        return self.json_ops.save_json("character.json", to_flat(char))

    def archive_character(self) -> Optional[str]:
        """Archive the outgoing character.json to fallen/, the way become() does."""
        old = self.json_ops.load_json("character.json")
        if not old:
            return None
        fallen_dir = self.campaign_dir / "fallen"
        fallen_dir.mkdir(parents=True, exist_ok=True)
        name = old.get("name") or "former-hero"
        slug = name.lower().replace(" ", "-")
        path = fallen_dir / f"{slug}-{old.get('id') or slug}.json"
        self.json_ops.save_json(str(path), old)
        return str(path)

    def _mark_as_pc(self, npc_name: str) -> None:
        """Flag the canon NPC as the PC so scene context stops voicing them as an NPC."""
        npcs = self.json_ops.load_json("npcs.json") or {}
        if npc_name in npcs:
            npcs[npc_name]["is_player_character"] = True
            npcs[npc_name]["is_party_member"] = False
            npcs[npc_name]["became_pc"] = True
            self.json_ops.save_json("npcs.json", npcs)

    def onboard(self, mode: str, replace: bool = False, **kw) -> Dict[str, Any]:
        """Build + persist an identity, wiring it in the way become() wires a swap.

        Refuses to overwrite an existing character.json unless `replace` is set;
        on replace the outgoing sheet is archived to fallen/ first. Returns a
        result dict (no printing) so the CLI owns the human/JSON split.
        """
        existing = self.json_ops.load_json("character.json")
        if existing and not replace:
            who = existing.get("name", "an existing character")
            return {"success": False,
                    "error": f'this campaign already plays "{who}" — pass --replace to hand the story to someone new'}

        char = self.build(mode, **kw)
        if char is None:
            return {"success": False,
                    "error": f'no NPC named "{kw.get("npc_name", "")}" in this campaign'}

        archived = self.archive_character() if existing else None

        if not self.save_character(char):
            return {"success": False, "error": "failed to save character.json"}

        saved = self.json_ops.load_json("character.json") or {}
        name = saved.get("name", "")
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        unmatched = not overview.get("opening_matched_to_pc")
        # Make the PC visible to session start / status / world_stats.
        self.json_ops.update_json("campaign-overview.json", {"current_character": name})
        if char.get("origin") == "canon":
            self._mark_as_pc(name)

        # First PC: import / /new-game hand off here and never call set.
        # Same gate as set_current_player — a PC-matched opening is left
        # alone so death-handoff --replace doesn't rewrite location/plot/log.
        if unmatched:
            from opening_seed import reseed_opening
            reseed_opening(str(self.campaign_dir), saved)

        return {"success": True, "character": saved, "archived": archived}


_SUMMARY_KEYS = ('name', 'race', 'class', 'level', 'hp', 'ac', 'stats',
                 'origin', 'concept', 'voice')


def main():
    """CLI: `onboard <canon|original|nameless> [args]` — the default entry path."""
    import argparse

    parser = argparse.ArgumentParser(description='Identity-first onboarding ("Who are you in this world?")')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    onboard = subparsers.add_parser('onboard', help='Create + persist the campaign character')
    onboard.add_argument('mode', choices=['canon', 'original', 'nameless'])
    onboard.add_argument('name', nargs='?',
                         help='canon: the NPC to play · original: the character name')
    onboard.add_argument('concept', nargs='?', default='',
                         help='original: a one-line concept')
    onboard.add_argument('--replace', action='store_true',
                         help='hand the story to a new PC (archives the current one to fallen/)')

    from cli_output import wants_json, strip_json_flag, emit, emit_error
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = IdentityOnboarding()

    if args.mode == 'canon':
        if not args.name:
            sys.exit(emit_error('canon mode needs an NPC name', json_mode))
        if args.concept:
            sys.exit(emit_error('canon mode takes only an NPC name', json_mode))
        kw = {'npc_name': args.name}
    elif args.mode == 'original':
        if not args.name:
            sys.exit(emit_error('original mode needs a character name', json_mode))
        kw = {'name': args.name, 'concept': args.concept}
    else:
        kw = {}

    result = manager.onboard(args.mode, replace=args.replace, **kw)
    if not result['success']:
        sys.exit(emit_error(result['error'], json_mode))

    saved = result['character']
    summary = {k: saved[k] for k in _SUMMARY_KEYS if k in saved}
    if result['archived']:
        summary['archived'] = result['archived']
    hp = saved.get('hp') or {}
    message = (f"✓ {saved.get('name', 'Unknown')} enters the world "
               f"({saved.get('origin', 'original')} · level {saved.get('level', 1)} · "
               f"HP {hp.get('current', '?')}/{hp.get('max', '?')})")
    if result['archived']:
        message += f"\nArchived the outgoing hero to: {result['archived']}"
    emit(summary, message=message, json_mode=json_mode)


if __name__ == '__main__':
    main()
