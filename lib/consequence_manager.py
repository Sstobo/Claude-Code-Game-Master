#!/usr/bin/env python3
"""
Consequence management module for GM tools
Handles tracking future events and consequences
"""

import sys
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager, npcs_present


class ConsequenceManager(EntityManager):
    """Manage consequence/event tracking. Inherits from EntityManager for common functionality."""

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.consequences_file = "consequences.json"
        self._ensure_file()

    def _ensure_file(self):
        """Ensure consequences file has proper structure"""
        data = self.json_ops.load_json(self.consequences_file)
        if not isinstance(data, dict) or 'active' not in data:
            data = {'active': [], 'resolved': []}
            self.json_ops.save_json(self.consequences_file, data)

    # Structured trigger types the reactivity engine can evaluate automatically.
    TRIGGER_TYPES = ('on_location', 'on_npc', 'on_time', 'on_event')

    def add_consequence(self, description: str, trigger: str,
                        trigger_type: str = None, match: str = None,
                        expiry: str = None) -> str:
        """
        Add a new consequence.

        Free-text `trigger` is always kept (human-readable + fuzzy fallback).
        Optionally attach a STRUCTURED trigger the engine can fire/expire on:
          trigger_type: one of TRIGGER_TYPES (on_location/on_npc/on_time/on_event)
          match:        value compared against world state (location/npc/time/event keyword)
          expiry:       optional date or condition after which the consequence ages out
        Structured fields are additive; legacy consequences omit them.

        Returns the consequence ID.
        """
        data = self.json_ops.load_json(self.consequences_file)

        consequence_id = str(uuid.uuid4())[:8]
        consequence = {
            'id': consequence_id,
            'consequence': description,
            'trigger': trigger,
            'created': self.json_ops.get_timestamp()
        }
        if trigger_type:
            consequence['trigger_type'] = trigger_type
        if match is not None:
            consequence['match'] = match
        if expiry is not None:
            consequence['expiry'] = expiry

        if 'active' not in data:
            data['active'] = []
        data['active'].append(consequence)

        if self.json_ops.save_json(self.consequences_file, data):
            print(f"[SUCCESS] Added consequence [{consequence_id}]: {description} (triggers: {trigger})")
            return consequence_id
        return ""

    def check_pending(self, world_state: Dict[str, Any] = None,
                      limit: int = 2) -> List[Dict[str, Any]]:
        """
        Pending consequences.

        - No world_state  -> the raw active list (legacy accessor).
        - With world_state -> only consequences that FIRE now, each annotated with
          a `match_reason`, sorted by confidence and capped at `limit`. Structured
          triggers match exactly; legacy free-text triggers are scored fuzzily.
          Expired consequences (past their `expiry`) are auto-archived to resolved.

        world_state keys (all optional): location (str), present_npcs (list[str]),
        time (str), events (list[str]), date (str).

        Firing does NOT remove a consequence — the GM vetoes for timing or resolves
        it explicitly; the tick layer dedups so it does not re-fire every beat.
        """
        data = self.json_ops.load_json(self.consequences_file)
        active = data.get('active', [])

        if world_state is None:
            return active

        fired = []
        survivors = []
        expired = []
        for c in active:
            if self._is_expired(c, world_state):
                aged = dict(c)
                aged['expired'] = self.json_ops.get_timestamp()
                expired.append(aged)
                continue
            survivors.append(c)
            score, reason = self._evaluate_trigger(c, world_state)
            if score > 0:
                hit = dict(c)
                hit['match_reason'] = reason
                fired.append((score, hit))

        if expired:
            data['active'] = survivors
            data.setdefault('resolved', []).extend(expired)
            self.json_ops.save_json(self.consequences_file, data)

        fired.sort(key=lambda t: t[0], reverse=True)
        return [hit for _, hit in fired[:limit]]

    @staticmethod
    def _world_text(world_state: Dict[str, Any]) -> str:
        parts = [
            str(world_state.get('location', '')),
            str(world_state.get('time', '')),
            str(world_state.get('date', '')),
            ' '.join(str(x) for x in world_state.get('present_npcs', []) or []),
            ' '.join(str(x) for x in world_state.get('events', []) or []),
        ]
        return ' '.join(parts).lower()

    def _is_expired(self, consequence: Dict[str, Any], world_state: Dict[str, Any]) -> bool:
        expiry = consequence.get('expiry')
        if not expiry:
            return False
        # Whole-word match, not substring: --expiry "dawn" must not self-archive
        # the moment the party stands anywhere named "Dawnhollow".
        import re
        pattern = r'\b' + re.escape(str(expiry).lower()) + r'\b'
        return re.search(pattern, self._world_text(world_state)) is not None

    def _evaluate_trigger(self, consequence: Dict[str, Any], world_state: Dict[str, Any]):
        """Return (score, reason). score 0 = no fire. Structured = 1.0; fuzzy < 1."""
        ttype = consequence.get('trigger_type')
        match = str(consequence.get('match', '')).lower()

        if ttype and match:
            if ttype == 'on_location' and match in str(world_state.get('location', '')).lower():
                return 1.0, f"at location matching '{consequence['match']}'"
            if ttype == 'on_npc':
                npcs = ' '.join(str(x) for x in world_state.get('present_npcs', []) or []).lower()
                if match in npcs:
                    return 1.0, f"NPC matching '{consequence['match']}' present"
            if ttype == 'on_time' and match in str(world_state.get('time', '')).lower():
                return 1.0, f"time matching '{consequence['match']}'"
            if ttype == 'on_event':
                events = ' '.join(str(x) for x in world_state.get('events', []) or []).lower()
                if match in events:
                    return 1.0, f"event matching '{consequence['match']}'"
            return 0.0, ''

        # Legacy free-text: score word overlap between the trigger phrase and world.
        world_text = self._world_text(world_state)
        stop = {'the', 'a', 'an', 'or', 'and', 'if', 'when', 'party', 'to', 'in', 'on',
                'at', 'of', 'for', 'more', 'than', 'again', 'next', 'with', 'makes'}
        words = {w.strip('.,;:\'"') for w in str(consequence.get('trigger', '')).lower().split()}
        words = {w for w in words if w and w not in stop and len(w) > 2}
        if not words:
            return 0.0, ''
        hits = [w for w in words if w in world_text]
        score = len(hits) / len(words)
        if score >= 0.5:
            return score, f"fuzzy match on: {', '.join(sorted(hits))}"
        return 0.0, ''

    def tick(self, world_state: Dict[str, Any], limit: int = 2) -> List[Dict[str, Any]]:
        """Fire matching consequences ONCE per context, stamping last_fired_key.

        Same scene (location|time|date) won't re-fire the same consequence; a
        changed scene re-arms it. Expired consequences are archived. Returns the
        newly-fired consequences (with match_reason). The GM may still veto a
        fired consequence narratively — it stays active either way.
        """
        data = self.json_ops.load_json(self.consequences_file)
        active = data.get('active', [])
        # Pre-fire snapshot for one-beat rollback (shallow copies; fields are scalar).
        pre_active = [dict(c) for c in active]
        pre_resolved = [dict(c) for c in data.get('resolved', [])]
        ctx_key = "|".join([
            str(world_state.get('location', '')),
            str(world_state.get('time', '')),
            str(world_state.get('date', '')),
        ]).lower()

        survivors, expired, candidates = [], [], []
        for c in active:
            if self._is_expired(c, world_state):
                aged = dict(c)
                aged['expired'] = self.json_ops.get_timestamp()
                expired.append(aged)
                continue
            survivors.append(c)
            score, reason = self._evaluate_trigger(c, world_state)
            if score > 0 and c.get('last_fired_key') != ctx_key:
                candidates.append((score, c, reason))

        candidates.sort(key=lambda t: t[0], reverse=True)
        fired = []
        for _score, c, reason in candidates[:limit]:
            c['last_fired_key'] = ctx_key  # stamp the live object (in survivors)
            hit = dict(c)
            hit['match_reason'] = reason
            fired.append(hit)

        if expired or fired:
            data['active'] = survivors
            if expired:
                data.setdefault('resolved', []).extend(expired)
            # Provenance ("why did this fire") + one-beat rollback snapshot.
            data['_snapshot'] = {'active': pre_active, 'resolved': pre_resolved}
            now = self.json_ops.get_timestamp()
            prov = data.setdefault('provenance', [])
            for hit in fired:
                prov.append({
                    'id': hit['id'],
                    'consequence': hit['consequence'],
                    'reason': hit['match_reason'],
                    'ctx_key': ctx_key,
                    'fired_at': now,
                })
            self.json_ops.save_json(self.consequences_file, data)
        return fired

    def get_provenance(self) -> List[Dict[str, Any]]:
        """Return the 'why did this fire' log (newest last)."""
        data = self.json_ops.load_json(self.consequences_file)
        return data.get('provenance', [])

    def rollback_last(self) -> bool:
        """Undo the most recent reactive beat (restore active/resolved to pre-fire)."""
        data = self.json_ops.load_json(self.consequences_file)
        snap = data.get('_snapshot')
        if not snap:
            print("[ERROR] No reactive beat to roll back")
            return False
        data['active'] = snap.get('active', data.get('active', []))
        data['resolved'] = snap.get('resolved', data.get('resolved', []))
        data['_snapshot'] = None
        if self.json_ops.save_json(self.consequences_file, data):
            print("[SUCCESS] Rolled back the last reactive beat")
            return True
        return False

    def tick_from_session(self, limit: int = 2) -> List[Dict[str, Any]]:
        """Build world_state from current campaign state, then tick()."""
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        pos = overview.get("player_position", {})
        location = pos.get("current_location", "") if isinstance(pos, dict) else ""
        npcs = self.json_ops.load_json("npcs.json") or {}
        present = list(npcs_present(npcs, location).keys())
        world_state = {
            "location": location,
            "time": overview.get("time_of_day", ""),
            "date": overview.get("current_date", ""),
            "present_npcs": present,
            "events": [],
        }
        return self.tick(world_state, limit=limit)

    def resolve(self, consequence_id: str) -> bool:
        """
        Resolve a consequence by ID
        """
        data = self.json_ops.load_json(self.consequences_file)

        resolved = None
        remaining = []

        for c in data.get('active', []):
            if c['id'] == consequence_id:
                resolved = c
                resolved['resolved'] = self.json_ops.get_timestamp()
                if 'resolved' not in data:
                    data['resolved'] = []
                data['resolved'].append(resolved)
            else:
                remaining.append(c)

        if resolved:
            data['active'] = remaining
            if self.json_ops.save_json(self.consequences_file, data):
                print(f"[SUCCESS] Resolved: {resolved['consequence']}")
                return True
        else:
            print(f"[ERROR] Consequence '{consequence_id}' not found")

        return False

    def list_resolved(self) -> List[Dict[str, Any]]:
        """
        Get all resolved consequences
        """
        data = self.json_ops.load_json(self.consequences_file)
        return data.get('resolved', [])


def main():
    """CLI interface for consequence management"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Consequence management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Add consequence
    add_parser = subparsers.add_parser('add', help='Add new consequence')
    add_parser.add_argument('description', help='Consequence description')
    add_parser.add_argument('trigger', help='Trigger condition (free-text)')
    add_parser.add_argument('--trigger-type', dest='trigger_type',
                            choices=list(ConsequenceManager.TRIGGER_TYPES),
                            help='Structured trigger type (enables auto-firing)')
    add_parser.add_argument('--match', help='Structured trigger match value')
    add_parser.add_argument('--expiry', help='Optional expiry (date or condition)')

    # Check pending
    subparsers.add_parser('check', help='Check pending consequences')

    # Tick (reactivity): fire matching consequences for the current scene
    subparsers.add_parser('tick', help='Fire consequences whose triggers match the current scene')

    # Provenance + rollback
    subparsers.add_parser('log', help='Show the reactive firing provenance log')
    subparsers.add_parser('rollback', help='Undo the most recent reactive beat')

    # Resolve
    resolve_parser = subparsers.add_parser('resolve', help='Resolve a consequence')
    resolve_parser.add_argument('id', help='Consequence ID')

    # List resolved
    subparsers.add_parser('list-resolved', help='List resolved consequences')

    from cli_output import wants_json, strip_json_flag, emit, emit_error
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = ConsequenceManager()

    if json_mode and args.action == 'add':
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):  # keep stdout JSON-only
            cid = manager.add_consequence(args.description, args.trigger,
                                          trigger_type=args.trigger_type,
                                          match=args.match, expiry=args.expiry)
        if cid:
            emit({"id": cid}, json_mode=True)
        else:
            sys.exit(emit_error("failed to add consequence", json_mode=True))
        return
    if json_mode and args.action == 'check':
        emit({"pending": manager.check_pending()}, json_mode=True)
        return

    if args.action == 'add':
        if not manager.add_consequence(args.description, args.trigger,
                                       trigger_type=args.trigger_type,
                                       match=args.match, expiry=args.expiry):
            sys.exit(1)

    elif args.action == 'check':
        pending = manager.check_pending()
        if not pending:
            print("No pending consequences")
        else:
            print(f"{len(pending)} pending consequences:")
            for c in pending:
                print(f"  [{c['id']}] {c['consequence']} (triggers: {c['trigger']})")

    elif args.action == 'tick':
        fired = manager.tick_from_session()
        if fired:
            print(f"[REACTIVITY] {len(fired)} consequence(s) fired this scene:")
            for c in fired:
                print(f"  [{c['id']}] {c['consequence']}")
                print(f"      ↳ fired because: {c['match_reason']} (veto if the timing's wrong)")
        else:
            print("[REACTIVITY] (nothing triggered here)")

    elif args.action == 'log':
        prov = manager.get_provenance()
        if not prov:
            print("No reactive firings logged")
        else:
            print(f"{len(prov)} reactive firing(s):")
            for p in prov:
                print(f"  [{p['id']}] {p['consequence']}")
                print(f"      ↳ {p['reason']} @ {p['fired_at']}")

    elif args.action == 'rollback':
        if not manager.rollback_last():
            sys.exit(1)

    elif args.action == 'resolve':
        if not manager.resolve(args.id):
            sys.exit(1)

    elif args.action == 'list-resolved':
        resolved = manager.list_resolved()
        if resolved:
            print(json.dumps(resolved, indent=2))
        else:
            print("No resolved consequences")


if __name__ == "__main__":
    main()
