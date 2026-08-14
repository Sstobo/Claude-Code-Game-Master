#!/usr/bin/env python3
"""
World Author — serial consolidator for the authored-world creation pipeline.

`/new-game` fans out parallel author subagents; each writes ONLY its own files
(`canon/<axis>.md` prose + `authored/<axis>.json` structured contributions) so the
fan-out is race-free. This module runs AFTER fan-out, single-threaded, and folds
those contributions into the campaign's runtime state — exactly the
"parallel author -> serial normalize" pattern the import pipeline uses.

Two commands:
  consolidate [campaign]   merge authored/*.json -> locations/npcs/facts.json
                           + world-bible.json (graphs deduped, confirmed preserved)
  compile-canon [campaign] concat bible preamble + canon/*.md -> authored-canon.md
                           (ready for `gm-extract.sh prepare` to embed for RAG)

`authored/<axis>.json` contract (only the keys an axis owns):
  {
    "locations": {Name: {position, connections:[{to,path}], description}},
    "npcs":      {Name: {description, attitude, tags:{locations:[],quests:[]}}},
    "plots":     {Name: {type, description, npcs:[], locations:[], status}},
    "facts":     {<category>: [ "fact" | {"fact": "..."} ]},
    "bible":     {factions:{nodes,edges}, geography:{nodes,edges}, timeline:[...],
                  signature_systems:[...], voice:{...}, themes:[...]}
  }

Existing root entries always win — re-running is idempotent and never resets a
location's `discovered`, an NPC's `created`/`events`, or duplicates graph nodes.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from campaign_manager import CampaignManager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sig(obj: Any) -> str:
    """Stable signature for dedupe of dict/list graph elements."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


class WorldAuthor:
    """Consolidates authored fan-out output into campaign runtime state."""

    def __init__(self, world_state_dir: str = None, campaign: str = None):
        base = world_state_dir or "world-state"
        cm = CampaignManager(base)
        self.campaign_dir = cm.get_campaign_path(campaign) if campaign else cm.get_active_campaign_dir()
        if not self.campaign_dir:
            raise ValueError("No campaign found (pass a name or set an active campaign)")
        self.campaign_dir = Path(self.campaign_dir)
        self.json_ops = JsonOperations(str(self.campaign_dir))
        self.authored_dir = self.campaign_dir / "authored"
        self.canon_dir = self.campaign_dir / "canon"

    # ---- authored input ----
    def _authored_files(self) -> List[Path]:
        if not self.authored_dir.is_dir():
            return []
        return sorted(self.authored_dir.glob("*.json"))

    # ---- merge: locations ----
    def _merge_locations(self, root: Dict, incoming: Dict) -> int:
        added = 0
        for name, loc in (incoming or {}).items():
            if name in root:
                continue  # existing entry wins (idempotent, preserves discovered)
            entry = {
                "position": loc.get("position", ""),
                "connections": loc.get("connections", []),
                "description": loc.get("description", ""),
                "discovered": loc.get("discovered") or _now(),
            }
            root[name] = entry
            added += 1
        return added

    # ---- merge: npcs ----
    def _merge_npcs(self, root: Dict, incoming: Dict) -> int:
        added = 0
        for name, npc in (incoming or {}).items():
            if name in root:
                continue
            tags = npc.get("tags") or {}
            entry = {
                "description": npc.get("description", ""),
                "attitude": npc.get("attitude", "neutral"),
                "created": npc.get("created") or _now(),
                "events": npc.get("events", []),
                "tags": {
                    "locations": tags.get("locations", []),
                    "quests": tags.get("quests", []),
                },
            }
            if npc.get("current_mood"):
                entry["current_mood"] = npc["current_mood"]
            root[name] = entry
            added += 1
        return added

    # ---- merge: plots ----
    def _merge_plots(self, root: Dict, incoming: Dict) -> int:
        """Fold an axis's authored plots into plots.json.

        This is what makes an authored world open alive: `spine`, `seed-clocks`
        and `seed-opening` all read plots.json, so an axis that names its
        conflicts here gets a story arc, live pressure, and an opening location.
        """
        added = 0
        for name, plot in (incoming or {}).items():
            if name in root:
                continue  # existing entry wins (idempotent, preserves events/status)
            entry = {
                "name": plot.get("name") or name,
                "description": plot.get("description", ""),
                "type": plot.get("type", "side"),
                "npcs": plot.get("npcs", []),
                "locations": plot.get("locations", []),
                "status": plot.get("status", "active"),
            }
            for optional in ("objectives", "consequences"):
                if plot.get(optional):
                    entry[optional] = plot[optional]
            root[name] = entry
            added += 1
        return added

    # ---- merge: facts ----
    def _merge_facts(self, root: Dict, incoming: Dict) -> int:
        added = 0
        for category, items in (incoming or {}).items():
            bucket = root.setdefault(category, [])
            existing_text = {f.get("fact") for f in bucket if isinstance(f, dict)}
            for item in items or []:
                text = item.get("fact") if isinstance(item, dict) else item
                if not text or text in existing_text:
                    continue
                bucket.append({"fact": text, "timestamp": _now()})
                existing_text.add(text)
                added += 1
        return added

    # ---- merge: bible ----
    @staticmethod
    def _merge_graph(base: Dict, frag: Dict) -> None:
        base.setdefault("nodes", [])
        base.setdefault("edges", [])
        seen_nodes = {n.get("name") or _sig(n) for n in base["nodes"]}
        for node in frag.get("nodes", []):
            key = node.get("name") or _sig(node)
            if key not in seen_nodes:
                base["nodes"].append(node)
                seen_nodes.add(key)
        seen_edges = {_sig(e) for e in base["edges"]}
        for edge in frag.get("edges", []):
            if _sig(edge) not in seen_edges:
                base["edges"].append(edge)
                seen_edges.add(_sig(edge))

    @staticmethod
    def _append_dedupe(base_list: List, frag_list: List) -> None:
        seen = {_sig(x) for x in base_list}
        for item in frag_list or []:
            if _sig(item) not in seen:
                base_list.append(item)
                seen.add(_sig(item))

    def _merge_bible(self, bible: Dict, frag: Dict) -> None:
        if not frag:
            return
        for graph_key in ("factions", "geography"):
            if graph_key in frag:
                self._merge_graph(bible.setdefault(graph_key, {"nodes": [], "edges": []}), frag[graph_key])
        for list_key in ("themes", "timeline", "signature_systems"):
            if list_key in frag:
                self._append_dedupe(bible.setdefault(list_key, []), frag[list_key])
        if "voice" in frag:
            voice = bible.setdefault("voice", {})
            for k, v in frag["voice"].items():
                if k == "sample_passages":
                    self._append_dedupe(voice.setdefault("sample_passages", []), v)
                elif k not in voice or not voice.get(k):
                    voice[k] = v  # skeleton voice wins; fragment fills gaps

    # ---- consolidate ----
    def consolidate(self) -> Dict[str, Any]:
        locations = self.json_ops.load_json("locations.json") or {}
        npcs = self.json_ops.load_json("npcs.json") or {}
        plots = self.json_ops.load_json("plots.json") or {}
        facts = self.json_ops.load_json("facts.json") or {}
        bible = self.json_ops.load_json("world-bible.json") or {}

        report = {"files": 0, "locations": 0, "npcs": 0, "plots": 0, "facts": 0, "bible_merged": False}
        for path in self._authored_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                report.setdefault("errors", []).append(f"{path.name}: {e}")
                continue
            report["files"] += 1
            report["locations"] += self._merge_locations(locations, data.get("locations", {}))
            report["npcs"] += self._merge_npcs(npcs, data.get("npcs", {}))
            report["plots"] += self._merge_plots(plots, data.get("plots", {}))
            report["facts"] += self._merge_facts(facts, data.get("facts", {}))
            if data.get("bible"):
                self._merge_bible(bible, data["bible"])
                report["bible_merged"] = True

        # Only write files we actually have content for (don't clobber with {}).
        if locations:
            self.json_ops.save_json("locations.json", locations)
        if npcs:
            self.json_ops.save_json("npcs.json", npcs)
        if plots:
            self.json_ops.save_json("plots.json", plots)
        if facts:
            self.json_ops.save_json("facts.json", facts)
        if bible:
            self.json_ops.save_json("world-bible.json", bible)  # confirmed flag preserved (untouched)
        return report

    # ---- compile-canon ----
    def compile_canon(self, out_name: str = "authored-canon.md") -> Dict[str, Any]:
        parts: List[str] = []
        bible = self.json_ops.load_json("world-bible.json") or {}
        if bible:
            preamble = [f"# {bible.get('name', 'Untitled World')}"]
            if bible.get("tone"):
                preamble.append(f"\nTone: {bible['tone']}")
            themes = bible.get("themes") or []
            if themes:
                preamble.append("Themes: " + ", ".join(str(t) for t in themes))
            voice = bible.get("voice") or {}
            if voice.get("style"):
                preamble.append(f"Voice: {voice['style']}")
            parts.append("\n".join(preamble))

        if self.canon_dir.is_dir():
            for md in sorted(self.canon_dir.glob("*.md")):
                try:
                    text = md.read_text(encoding="utf-8").strip()
                except OSError:
                    continue
                if text:
                    parts.append(text)

        body = "\n\n---\n\n".join(p for p in parts if p.strip())
        out_path = self.campaign_dir / out_name
        out_path.write_text(body + "\n", encoding="utf-8")
        return {"path": str(out_path), "bytes": len(body), "sections": len(parts)}


def main():
    import argparse
    from cli_output import wants_json, strip_json_flag, emit, emit_error

    json_mode = wants_json()
    argv = strip_json_flag(sys.argv[1:])
    parser = argparse.ArgumentParser(description="World Author — consolidate authored fan-out output")
    sub = parser.add_subparsers(dest="action")
    p_con = sub.add_parser("consolidate", help="merge authored/*.json into campaign state")
    p_con.add_argument("campaign", nargs="?", default=None)
    p_cmp = sub.add_parser("compile-canon", help="concat bible + canon/*.md into one text file")
    p_cmp.add_argument("campaign", nargs="?", default=None)
    args = parser.parse_args(argv)

    if not args.action:
        parser.print_help()
        sys.exit(2)

    try:
        wa = WorldAuthor(campaign=args.campaign)
    except ValueError as e:
        sys.exit(emit_error(str(e), json_mode=json_mode))

    if args.action == "consolidate":
        result = wa.consolidate()
    else:
        result = wa.compile_canon()

    if json_mode:
        emit(result, json_mode=True)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
