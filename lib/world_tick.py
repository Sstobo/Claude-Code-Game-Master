#!/usr/bin/env python3
"""
Between-session world tick — the world keeps living when you look away.

On session end/start a world-builder pass proposes 1-3 SMALL off-screen
developments (grounded in source RAG + existing plots — that generation is a
model call in /dm). This module owns the deterministic, safe machinery: enforce
the cap, write each development as a consequence, log the tick for provenance, and
allow a one-tick rollback so a misfire never silently rewrites the world.
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

    def apply(self, developments: List[Dict[str, Any]], cap: int = 3, enabled: bool = True) -> List[Dict[str, Any]]:
        """Write up to `cap` proposed developments as consequences. enabled=False = no-op (tone)."""
        if not enabled or not developments:
            return []
        applied = []
        for d in developments[:cap]:
            text = d.get("text", "")
            if not text:
                continue
            cid = self.cm.add_consequence(
                text, d.get("trigger", "off-screen development"),
                trigger_type=d.get("trigger_type"), match=d.get("match"))
            if cid:
                applied.append({"id": cid, "text": text, "source": "world-tick"})

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
