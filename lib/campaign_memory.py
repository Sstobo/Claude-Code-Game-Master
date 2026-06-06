#!/usr/bin/env python3
"""
Long-term campaign memory — so a 50-session campaign remembers itself.

Builds a recall index over the campaign's OWN lived history (session summaries +
facts) and maintains a tiered, consolidating memoir (always-on arc summary +
recent verbatim + compressed older + retrievable archive) so memory stays
high-signal and bounded. A provenance dimension separates book-canon from
our-story so the huge imported world stays out of always-loaded context while the
threads you actually touched surface. session-log.md remains the canonical ledger
— this only reads it.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager

_CANON_CATEGORIES = {"plot_world", "world_building"}


class CampaignMemory(EntityManager):
    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.memory_file = "campaign-memory.json"

    def gather(self) -> List[Dict[str, Any]]:
        """Collect memory entries from the campaign's own history (read-only)."""
        entries: List[Dict[str, Any]] = []

        log_path = self.campaign_dir / "session-log.md"
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            for block in text.split("## Session Started:"):
                if "### Session Ended:" not in block:
                    continue
                after = block.split("### Session Ended:", 1)[1]
                body = []
                for ln in after.splitlines()[1:]:
                    s = ln.strip()
                    if s == "---":
                        break
                    if s and not s.startswith("**"):  # skip the structured footer lines
                        body.append(s)
                if body:
                    entries.append({"text": " ".join(body), "provenance": "our-story",
                                    "source": "session-log", "tier": "recent"})

        facts = self.json_ops.load_json("facts.json") or {}
        if isinstance(facts, dict):
            for cat, items in facts.items():
                if not isinstance(items, list):
                    continue
                prov = "book-canon" if cat in _CANON_CATEGORIES else "our-story"
                for it in items:
                    t = it.get("fact") if isinstance(it, dict) else str(it)
                    if t:
                        entries.append({"text": t, "provenance": prov,
                                        "source": f"facts:{cat}", "tier": "archive"})
        return entries

    def refresh(self) -> int:
        """Rebuild the recall collection (called on save)."""
        entries = self.gather()
        self.json_ops.save_json(self.memory_file, {"entries": entries})
        return len(entries)

    def recall(self, query: str, top_k: int = 3, provenance: str = None) -> List[Dict[str, Any]]:
        """Semantic-ish recall (keyword overlap) over the campaign's history."""
        data = self.json_ops.load_json(self.memory_file) or {}
        entries = data.get("entries") or self.gather()
        if provenance:
            entries = [e for e in entries if e.get("provenance") == provenance]
        q = set(re.findall(r"\w+", query.lower()))
        if not q:
            return []
        scored = []
        for e in entries:
            tw = set(re.findall(r"\w+", e["text"].lower()))
            s = len(q & tw)
            if s > 0:
                scored.append((s, e))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def memoir(self) -> Dict[str, Any]:
        """Tiered, bounded memoir: arc summary + recent verbatim + counts."""
        entries = self.gather()
        recent = [e for e in entries if e["tier"] == "recent"]
        archive = [e for e in entries if e["tier"] == "archive"]
        arc = recent[-1]["text"][:300] if recent else ""
        return {
            "arc_summary": arc,
            "recent": recent[-3:],
            "compressed_older": max(0, len(recent) - 3),
            "archive_count": len(archive),
            "canon_count": sum(1 for e in entries if e["provenance"] == "book-canon"),
        }


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit

    parser = argparse.ArgumentParser(description="Campaign memory")
    sub = parser.add_subparsers(dest="action")
    r = sub.add_parser("recall"); r.add_argument("query", nargs="+")
    r.add_argument("--provenance", choices=["our-story", "book-canon"])
    sub.add_parser("refresh")
    sub.add_parser("memoir")

    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        parser.print_help(); sys.exit(1)

    m = CampaignMemory()
    if args.action == "recall":
        out = m.recall(" ".join(args.query), provenance=getattr(args, "provenance", None))
    elif args.action == "refresh":
        out = {"indexed": m.refresh()}
    else:
        out = m.memoir()

    if json_mode:
        emit(out, json_mode=True)
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
