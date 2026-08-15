#!/usr/bin/env python3
"""
The Book Bible — the structured fidelity spine of a world.

world-bible.json is what makes "playing Dune" feel unmistakably like Dune rather
than d20-fantasy-in-a-desert. It captures VOICE, TONE, THEMES, FACTIONS (as a
graph), GEOGRAPHY (as a place graph), TIMELINE, and the book's SIGNATURE SYSTEMS,
and is the canonical spine loaded at session start. The import pipeline
(import-longcontext-read) auto-drafts it; here we define + validate the shape and
ship a hand-authored DCC bible to prove it.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from campaign_manager import CampaignManager

_REQUIRED = ('name', 'voice', 'tone', 'themes', 'factions', 'geography', 'signature_systems')


def _is_graph(g: Any) -> bool:
    return isinstance(g, dict) and isinstance(g.get('nodes'), list) and isinstance(g.get('edges'), list)


_INDEX_BUCKETS = ('npcs', 'locations', 'items', 'monsters')


def _index_errors(index: Any) -> List[str]:
    """Validate the optional `index` roster: a dict of four buckets, each a list
    of {"name","note"} objects. Absent is valid (legacy bibles); malformed fails.
    """
    if not isinstance(index, dict):
        return ['index must be an object {npcs:[], locations:[], items:[], monsters:[]}']
    errors: List[str] = []
    for bucket in _INDEX_BUCKETS:
        entries = index.get(bucket, [])
        if not isinstance(entries, list):
            errors.append(f'index.{bucket} must be a list')
            continue
        for entry in entries:
            if not (isinstance(entry, dict) and isinstance(entry.get('name'), str)
                    and isinstance(entry.get('note'), str)):
                errors.append(f'index.{bucket} entries must be {{"name","note"}} objects')
                break
    return errors


def validate_bible(bible: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(bible, dict):
        return False, ['world-bible must be an object']
    for key in _REQUIRED:
        if key not in bible:
            errors.append(f'missing required key: {key}')
    if not isinstance(bible.get('themes', []), list):
        errors.append('themes must be a list')
    if not isinstance(bible.get('signature_systems', []), list):
        errors.append('signature_systems must be a list')
    if 'factions' in bible and not _is_graph(bible['factions']):
        errors.append('factions must be a graph {nodes:[], edges:[]}')
    if 'geography' in bible and not _is_graph(bible['geography']):
        errors.append('geography must be a graph {nodes:[], edges:[]}')
    voice = bible.get('voice')
    if voice is not None and not isinstance(voice, dict):
        errors.append('voice must be an object (style/vocab/sample_passages)')
    if 'index' in bible:
        errors.extend(_index_errors(bible['index']))
    return (len(errors) == 0), errors


class WorldBible:
    """Loads + exposes a campaign's world-bible.json."""

    def __init__(self, world_state_dir: str = None):
        base = world_state_dir or "world-state"
        cm = CampaignManager(base)
        self.campaign_dir = cm.get_active_campaign_dir()
        self.json_ops = JsonOperations(str(self.campaign_dir))
        self.bible = self.json_ops.load_json("world-bible.json") or {}

    def exists(self) -> bool:
        return bool(self.bible)

    def validate(self) -> Tuple[bool, List[str]]:
        return validate_bible(self.bible)

    def voice(self) -> Dict[str, Any]:
        return self.bible.get('voice', {})

    def factions(self) -> Dict[str, Any]:
        return self.bible.get('factions', {'nodes': [], 'edges': []})

    def geography(self) -> Dict[str, Any]:
        return self.bible.get('geography', {'nodes': [], 'edges': []})

    def signature_systems(self) -> List[Any]:
        return self.bible.get('signature_systems', [])

    # --- draft-then-confirm gate ---
    def is_confirmed(self) -> bool:
        """A newly-drafted bible is `confirmed: false` until a human approves it.

        Legacy campaigns / hand-authored bibles (no flag) count as confirmed so the
        gate only blocks freshly auto-drafted worlds.
        """
        return bool(self.bible.get('confirmed', True))

    def is_playable(self) -> bool:
        """A world is playable unless it has an unconfirmed auto-drafted bible."""
        if not self.bible:
            return True  # no bible (e.g. /new-game) -> nothing to confirm
        return self.is_confirmed()

    def confirm(self) -> bool:
        """Mark the drafted world approved + persist."""
        self.bible['confirmed'] = True
        return self.json_ops.save_json("world-bible.json", self.bible)

    def review_summary(self) -> Dict[str, Any]:
        """The human-facing draft to review before play (voice/factions/systems)."""
        return {
            'name': self.bible.get('name'),
            'tone': self.bible.get('tone'),
            'voice_style': self.voice().get('style'),
            'themes': self.bible.get('themes', []),
            # Faction nodes are authored by the model (or by hand): conan's live
            # bible lists them as bare strings, not {name: ...} objects. This is a
            # review screen — show what is there rather than crash on the shape.
            'factions': [n.get('name') if isinstance(n, dict) else n
                         for n in self.factions().get('nodes', [])],
            'signature_systems': self.signature_systems(),
            'confirmed': self.is_confirmed(),
        }


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit, emit_error

    parser = argparse.ArgumentParser(description="World Bible")
    parser.add_argument('action', nargs='?', default='validate',
                        choices=['validate', 'show', 'review', 'confirm'])
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    wb = WorldBible()
    if args.action == 'validate':
        ok, errs = wb.validate()
        result = {'valid': ok, 'errors': errs, 'name': wb.bible.get('name')}
        if json_mode:
            emit(result, json_mode=True)
        else:
            print(json.dumps(result, indent=2))
        sys.exit(0 if ok else 1)
    elif args.action == 'review':
        # The human-facing draft. A drafted world is `confirmed: false` until the
        # PLAYER approves what this prints — never confirm on their behalf.
        summary = wb.review_summary()
        if json_mode:
            emit(summary, json_mode=True)
        else:
            print(json.dumps(summary, indent=2))
    elif args.action == 'confirm':
        if not wb.exists():
            sys.exit(emit_error('no world-bible.json to confirm', json_mode))
        wb.confirm()
        emit({'confirmed': True, 'name': wb.bible.get('name')},
             message=f"World bible confirmed: {wb.bible.get('name')}", json_mode=json_mode)
    else:
        if json_mode:
            emit(wb.bible, json_mode=True)
        else:
            print(json.dumps(wb.bible, indent=2))


if __name__ == "__main__":
    main()
