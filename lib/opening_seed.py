#!/usr/bin/env python3
"""Seed the opening beat so a fresh import starts at the book's opening, not a void.

After cap/integrity/spine, this sets the campaign's starting player_position to the
arc's opening location, marks the first spine plot active with an opening beat, and
writes a session-log "Previously On / Where We Paused" block (the channel
get_full_context reads) so the first /gm session opens on the book's actual opening.

That pipeline call is *provisional*: there is no PC yet, so the campaign still has
to open somewhere. `reseed_opening` rewrites the same three artifacts together once
the PC first exists (`IdentityOnboarding.onboard`, or the first `set_current_player`
while `opening_matched_to_pc` is unset), so play's opening matches the protagonist.
Provisional `seed_opening` does not set that flag; `reseed_opening` does.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import resolve_entity_name


_OPENING_MARK_START = "<!-- opening-seed -->"
_OPENING_MARK_END = "<!-- /opening-seed -->"
_LEGACY_OPENING = re.compile(
    r"## Session Started: [^\n]+\n\n### Session Ended: [^\n]+\nOpening scene\..*?\n---\n*",
    re.DOTALL,
)
_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP = frozenset({
    "that", "this", "with", "from", "into", "your", "their", "have", "been",
    "were", "they", "them", "then", "when", "what", "which", "about", "after",
    "before", "there", "here", "will", "would", "could", "should", "into",
})


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


def _load(cdir: Path, name: str):
    p = cdir / name
    return json.loads(p.read_text()) if p.exists() else {}


def _spine_names(overview: dict, plots: dict) -> list:
    arc = (overview.get("story_spine") or {}).get("arc") or []
    names = [n for n in arc if n in plots and isinstance(plots[n], dict)]
    if names:
        return names
    return [n for n, p in plots.items() if isinstance(p, dict) and str(p.get("type")) == "main"]


def _tokens(text: str) -> set:
    return {t for t in _WORD_RE.findall((text or "").lower()) if len(t) >= 4 and t not in _STOP}


def _pc_identities(character: dict) -> list:
    names = []
    name = (character or {}).get("name")
    if name:
        names.append(str(name))
    for a in (character or {}).get("aliases") or []:
        if a:
            names.append(str(a))
    return names


def _pc_locations(character: dict) -> list:
    locs = []
    for key in ("current_location", "location", "starting_location"):
        v = (character or {}).get(key)
        if v:
            locs.append(str(v))
    return locs


def _pc_prose(character: dict) -> str:
    char = character or {}
    parts = [char.get(k, "") for k in (
        "name", "description", "background", "notes", "concept", "era", "class", "race",
    )]
    return " ".join(str(p) for p in parts if p)


def _score_plot(plot: dict, plot_name: str, character: dict) -> tuple:
    """(npc_hits, location_hits, description_overlap) — higher wins.

    ``plot.npcs`` entries that resolve to the PC themselves are ignored. The
    protagonist is listed on many plots (Conan on both king-era and pirate-era
    arcs); that hit must not outrank era/concept overlap.
    """
    npc_hits = 0
    pc_ids = _pc_identities(character)
    plot_npcs = [
        n for n in (plot.get("npcs") or [])
        if not resolve_entity_name(str(n), pc_ids)
    ]
    for ident in pc_ids:
        if resolve_entity_name(ident, plot_npcs):
            npc_hits += 1
    loc_hits = 0
    plot_locs = plot.get("locations") or []
    for loc in _pc_locations(character):
        if resolve_entity_name(loc, plot_locs):
            loc_hits += 1
    overlap = len(_tokens(_pc_prose(character)) & _tokens(f"{plot_name} {plot.get('description', '')}"))
    return (npc_hits, loc_hits, overlap)


def _pick_opening_plot(plots: dict, spine: list, character=None) -> str:
    """Choose which spine plot to open on.

    Match rule when a PC is provided and the arc has 2+ plots, in priority order
    (ties fall through; a remaining tie keeps the earlier spine position):

    1. PC ``name`` / ``aliases`` resolve against ``plot.npcs`` (alias-aware),
       ignoring entries that *are* the PC — the protagonist appears in many plots.
    2. A location the sheet carries (``current_location``, ``location``, or
       ``starting_location``) resolves against ``plot.locations``.
    3. Token overlap (≥4-letter words) between the sheet's name / description /
       background / notes / concept / era / class / race and the plot's name +
       description. After (1) drops the PC's own listings, era/concept overlap
       is what separates two arcs the protagonist appears in.

    A plot that scores (0, 0, 0) on all three is ignored in favor of any plot
    that scores; if every candidate is zero, keep spine position 1. With one
    spine plot or no PC, always spine position 1 (same as ``seed_opening``).
    """
    if not spine:
        return None
    if character is None or len(spine) == 1:
        return spine[0]
    best_name, best_score = spine[0], (0, 0, 0)
    for name in spine:
        score = _score_plot(plots[name], name, character)
        if score > best_score:
            best_name, best_score = name, score
    return best_name


def _opening_block(ts: str, hook: str, opening_loc: str, plot_name: str) -> str:
    return (
        f"{_OPENING_MARK_START}\n"
        f"## Session Started: {ts}\n\n"
        f"### Session Ended: {ts}\n"
        f"Opening scene. {hook}\n\n"
        f"**Session:** 0\n"
        f"**Location:** {opening_loc}\n"
        f"**Cliffhanger:** {hook}\n"
        f"**Open threads:** {plot_name}\n\n"
        f"---\n\n"
        f"{_OPENING_MARK_END}\n"
    )


def _swap_opening_log(existing: str, block: str) -> str:
    """Replace the marked (or legacy unmarked) opening-seed block; else append."""
    start = existing.find(_OPENING_MARK_START)
    end = existing.find(_OPENING_MARK_END)
    if start != -1 and end != -1 and end > start:
        end += len(_OPENING_MARK_END)
        while end < len(existing) and existing[end] == "\n":
            end += 1
        return existing[:start] + block + existing[end:]
    match = _LEGACY_OPENING.search(existing)
    if match:
        return existing[:match.start()] + block + existing[match.end():]
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + block


def _commit_opening(cdir: Path, overview: dict, plots: dict, log_text: str) -> None:
    """Write position + plots + session-log together. Partial write is the bug."""
    ov_tmp = cdir / "campaign-overview.json.tmp"
    plots_tmp = cdir / "plots.json.tmp"
    log_tmp = cdir / "session-log.md.tmp"
    ov_tmp.write_text(json.dumps(overview, indent=2), encoding="utf-8")
    plots_tmp.write_text(json.dumps(plots, indent=2), encoding="utf-8")
    log_tmp.write_text(log_text, encoding="utf-8")
    ov_tmp.replace(cdir / "campaign-overview.json")
    plots_tmp.replace(cdir / "plots.json")
    log_tmp.replace(cdir / "session-log.md")


def _activate_opening_plot(plots: dict, chosen: str, spine: list, ts: str, hook: str, demote_others: bool) -> None:
    """Mark ``chosen`` active with an opening beat. On re-seed, other spine plots
    that were the previous opening return to ``available`` — exactly one spine
    plot stays ``active``."""
    beat = f"Opening beat: {hook}"
    for name, plot in plots.items():
        if not isinstance(plot, dict):
            continue
        if name == chosen:
            plot["status"] = "active"
            events = plot.setdefault("events", [])
            if not any(isinstance(e, dict) and e.get("event") == beat for e in events):
                events.append({"event": beat, "timestamp": ts})
        elif demote_others and name in spine and str(plot.get("status", "")).lower() == "active":
            plot["status"] = "available"


def _apply_opening(campaign_dir, character=None, timestamp=None, *, reseed=False) -> dict:
    cdir = Path(campaign_dir)
    ts = timestamp or _now()

    overview = _load(cdir, "campaign-overview.json")
    plots = _load(cdir, "plots.json")
    locations = _load(cdir, "locations.json")

    spine = _spine_names(overview, plots)
    chosen = _pick_opening_plot(plots, spine, character if reseed else None)
    if not chosen or chosen not in plots:
        return {"seeded": False, "reason": "no main/spine plot to open on"}

    first_plot = plots[chosen]
    opening_loc = _opening_location(first_plot, locations) or "Unknown"
    hook = _first_sentences(first_plot.get("description", ""), 2) or f"The adventure begins: {chosen}."

    pos = overview.get("player_position") or {}
    if not isinstance(pos, dict):
        pos = {}
    pos["current_location"] = opening_loc
    overview["player_position"] = pos
    if reseed:
        overview["opening_matched_to_pc"] = True

    _activate_opening_plot(plots, chosen, set(spine), ts, hook, demote_others=reseed)

    log_path = cdir / "session-log.md"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    log_text = _swap_opening_log(existing, _opening_block(ts, hook, opening_loc, chosen))

    _commit_opening(cdir, overview, plots, log_text)
    return {"seeded": True, "opening_location": opening_loc, "first_plot": chosen, "hook": hook}


def seed_opening(campaign_dir, timestamp=None) -> dict:
    """Provisional seed (import / new-game pipeline). Opens on spine[0] / first main."""
    return _apply_opening(campaign_dir, character=None, timestamp=timestamp, reseed=False)


def reseed_opening(campaign_dir, character, timestamp=None) -> dict:
    """Rewrite the opening once the PC exists.

    Atomic: starting location, active plot, and the session-log "Previously On"
    hook are computed then written together. The previously seeded spine plot
    returns to ``available`` so exactly one spine plot is ``active``. Plot
    selection uses `_pick_opening_plot` (PC-aware when the arc has 2+ plots).
    """
    return _apply_opening(campaign_dir, character=character, timestamp=timestamp, reseed=True)


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
