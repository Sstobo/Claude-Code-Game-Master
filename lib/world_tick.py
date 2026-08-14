#!/usr/bin/env python3
"""
Between-session world tick — the world keeps living when you look away.

On session end/start a world-builder pass proposes SMALL off-screen developments
(grounded in source RAG + existing plots — that generation is a model call in
/gm). This module owns the deterministic, safe machinery: write every proposed
development as a consequence, warn when the proposal count exceeds the advisory
cap (default 3), log the tick for provenance, and allow a one-tick rollback so a
misfire never silently rewrites the world.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from consequence_manager import ConsequenceManager


class WorldTick:
    def __init__(self, world_state_dir: str = None):
        self.cm = ConsequenceManager(world_state_dir)
        self.json_ops = self.cm.json_ops
        self.log_file = "world-tick-log.json"
        self.last_overflow: List[Dict[str, Any]] = []

    def apply(self, developments: List[Dict[str, Any]], cap: int = 3, enabled: bool = True) -> List[Dict[str, Any]]:
        """Write every proposed development as a consequence. enabled=False = no-op (tone).

        `cap` is advisory: all proposals apply, and anything past `cap` is named
        in a warning (stderr + `last_overflow`).
        """
        self.last_overflow: List[Dict[str, Any]] = []
        if not enabled or not developments:
            return []
        applied = []
        for d in developments:
            text = d.get("text", "")
            if not text:
                continue
            cid = self.cm.add_consequence(
                text, d.get("trigger", "off-screen development"),
                trigger_type=d.get("trigger_type"), match=d.get("match"))
            if cid:
                applied.append({"id": cid, "text": text, "source": "world-tick"})

        if len(applied) > cap:
            self.last_overflow = applied[cap:]
            names = ", ".join(a["text"] for a in self.last_overflow)
            print(f"[WORLD TICK] warning: cap {cap} exceeded; also applied: {names}",
                  file=sys.stderr)

        if applied:
            log = self.json_ops.load_json(self.log_file) or {"ticks": []}
            log["ticks"].append({
                "added": [a["id"] for a in applied],
                "at": self.json_ops.get_timestamp(),
                "developments": [a["text"] for a in applied],
            })
            if not self.json_ops.save_json(self.log_file, log):
                # Log write failed -> the just-added consequences would be
                # unrollback-able. Roll them back immediately to keep state clean.
                ids = {a["id"] for a in applied}
                data = self.json_ops.load_json("consequences.json") or {}
                data["active"] = [c for c in data.get("active", []) if c.get("id") not in ids]
                self.json_ops.save_json("consequences.json", data)
                return []
        return applied

    def rollback_last(self) -> bool:
        """Undo the most recent world tick (remove the consequences it added)."""
        log = self.json_ops.load_json(self.log_file) or {"ticks": []}
        if not log["ticks"]:
            return False
        last = log["ticks"][-1]
        ids = set(last.get("added", []))
        data = self.json_ops.load_json("consequences.json") or {}
        data["active"] = [c for c in data.get("active", []) if c.get("id") not in ids]
        # Only pop the log entry if the consequence removal actually persisted,
        # so a failed write never leaves the log and state inconsistent.
        if not self.json_ops.save_json("consequences.json", data):
            return False
        log["ticks"].pop()
        self.json_ops.save_json(self.log_file, log)
        return True

    def history(self) -> List[Dict[str, Any]]:
        return (self.json_ops.load_json(self.log_file) or {}).get("ticks", [])


def main():
    """CLI: the GM proposes developments (a model call in /gm); this persists them.

    apply '<json>'   json = [{"text": "...", "trigger": "...",
                              "trigger_type": "on_location", "match": "..."}]
    rollback         undo the most recent tick
    history          show all ticks
    """
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit, emit_error

    parser = argparse.ArgumentParser(description="Between-session world tick")
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("apply"); p.add_argument("developments", help="JSON list of developments")
    p.add_argument("--cap", type=int, default=3)
    sub.add_parser("rollback")
    sub.add_parser("history")

    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        parser.print_help(); sys.exit(1)

    wt = WorldTick()
    if args.action == "apply":
        try:
            devs = json.loads(args.developments)
        except ValueError:
            sys.exit(emit_error("developments must be a JSON list", json_mode=json_mode))
        if not isinstance(devs, list):
            sys.exit(emit_error("developments must be a JSON list", json_mode=json_mode))
        if json_mode:
            # add_consequence prints human lines; keep stdout JSON-only.
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                applied = wt.apply(devs, cap=args.cap)
            payload = {"applied": applied}
            overflow = getattr(wt, "last_overflow", []) or []
            if overflow:
                payload["overflow"] = overflow
                payload["warning"] = (
                    f"cap {args.cap} exceeded; also applied: "
                    + ", ".join(a["text"] for a in overflow)
                )
            emit(payload, json_mode=True)
        else:
            applied = wt.apply(devs, cap=args.cap)
            for a in applied:
                print(f"[WORLD TICK] [{a['id']}] {a['text']}")
            if not applied:
                print("[WORLD TICK] nothing applied")
    elif args.action == "rollback":
        ok = wt.rollback_last()
        if json_mode:
            emit({"rolled_back": ok}, json_mode=True)
        else:
            print("[WORLD TICK] rolled back last tick" if ok else "[WORLD TICK] nothing to roll back")
        if not ok:
            sys.exit(1)
    else:
        out = wt.history()
        if json_mode:
            emit({"ticks": out}, json_mode=True)
        else:
            print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
