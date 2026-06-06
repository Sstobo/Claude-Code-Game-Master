#!/usr/bin/env python3
"""Seed the opening beat so a fresh import starts at the book's opening, not a void.

After cap/integrity/spine, this sets the campaign's starting player_position to the
arc's opening location, marks the first spine plot active with an opening beat, and
writes a session-log "Previously On / Where We Paused" block (the channel
get_full_context reads) so the first /dm session opens on the book's actual opening.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import resolve_entity_name


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _first_sentences(text: str, n: int = 2) -> str:
    parts = [s.strip() for s in (text or "").replace("!", ".").replace("?", ".").split(".") if s.strip()]
    return (". ".join(parts[:n]) + ".") if parts else ""


def _hub(locations: dict):
    best, deg = None, -1
    for name, loc in locations.items():
        d = len((loc or {}).get("connections", []) or []) if isinstance(loc, dict) else 0
        if d > deg:
            best, deg = name, d
    return best


def _opening_location(first_plot: dict, locations: dict):
    for ref in (first_plot or {}).get("locations", []) or []:
        key = resolve_entity_name(ref, locations)
        if key:
            return key
    return _hub(locations) or (next(iter(locations), None))


def seed_opening(campaign_dir, timestamp=None) -> dict:
    """Seed opening position + beat + session-log hook. Returns a report."""
    cdir = Path(campaign_dir)
    ts = timestamp or _now()

    def _load(name):
        p = cdir / name
        return json.loads(p.read_text()) if p.exists() else {}

    overview = _load("campaign-overview.json")
    plots = _load("plots.json")
    locations = _load("locations.json")

    arc = (overview.get("story_spine") or {}).get("arc") or []
    first_name = arc[0] if arc else next(
        (n for n, p in plots.items() if isinstance(p, dict) and str(p.get("type")) == "main"), None)
    if not first_name or first_name not in plots:
        return {"seeded": False, "reason": "no main/spine plot to open on"}

    first_plot = plots[first_name]
    opening_loc = _opening_location(first_plot, locations) or "Unknown"
    hook = _first_sentences(first_plot.get("description", ""), 2) or f"The adventure begins: {first_name}."

    # 1. starting position (preserve other player_position fields)
    pos = overview.get("player_position") or {}
    if not isinstance(pos, dict):
        pos = {}
    pos["current_location"] = opening_loc
    overview["player_position"] = pos
    (cdir / "campaign-overview.json").write_text(json.dumps(overview, indent=2))

    # 2. mark first spine plot active + opening beat
    first_plot["status"] = "active"
    events = first_plot.setdefault("events", [])
    beat = f"Opening beat: {hook}"
    if not any(isinstance(e, dict) and e.get("event") == beat for e in events):
        events.append({"event": beat, "timestamp": ts})
    (cdir / "plots.json").write_text(json.dumps(plots, indent=2))

    # 3. session-log opening block (parseable by _recent_session_summaries + _latest_session_meta)
    log = cdir / "session-log.md"
    block = (
        f"## Session Started: {ts}\n\n"
        f"### Session Ended: {ts}\n"
        f"Opening scene. {hook}\n\n"
        f"**Session:** 0\n"
        f"**Location:** {opening_loc}\n"
        f"**Cliffhanger:** {hook}\n"
        f"**Open threads:** {first_name}\n\n"
        f"---\n\n"
    )
    with open(log, "a", encoding="utf-8") as f:
        f.write(block)

    return {"seeded": True, "opening_location": opening_loc, "first_plot": first_name, "hook": hook}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed the opening beat")
    parser.add_argument("campaign_dir")
    args = parser.parse_args()
    r = seed_opening(args.campaign_dir)
    if r.get("seeded"):
        print(f"  opening location: {r['opening_location']}")
        print(f"  first beat: {r['first_plot']}")
        print(f"  hook: {r['hook']}")
    else:
        print(f"  not seeded: {r.get('reason')}")


if __name__ == "__main__":
    main()
