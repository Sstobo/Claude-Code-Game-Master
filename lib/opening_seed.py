#!/usr/bin/env python3
"""Seed a provisional opening so a fresh import is not a void.

After cap/integrity/spine, this sets `player_position.current_location` and records
the chosen hook on `overview.opening_hook` and as a `plot_local` KEY FACT
(`Opening (not yet played): …`) so `get_full_context` already surfaces it. It
does not fabricate a session-log `### Session Ended` block (PREVIOUSLY ON is
earned play) and does not stamp a plot `active` or append an "Opening beat:"
event — plots stay as they were, typically `available`. `reseed_opening`
rewrites location + hook once the PC first exists (`IdentityOnboarding.onboard`,
or the first `set_current_player` while `opening_matched_to_pc` is unset) so
WHERE YOU STAND and WHICH HOOK is offered match the protagonist. It still does
not start that plot. Provisional `seed_opening` does not set the flag;
`reseed_opening` does.
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
_OPENING_FACT_PREFIX = "Opening (not yet played):"
_OPENING_FACT_CATEGORY = "plot_local"
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


def _strip_opening_log(existing: str) -> str:
    """Remove a marked (or legacy unmarked) opening-seed block. Leave real sessions."""
    start = existing.find(_OPENING_MARK_START)
    end = existing.find(_OPENING_MARK_END)
    if start != -1 and end != -1 and end > start:
        end += len(_OPENING_MARK_END)
        while end < len(existing) and existing[end] == "\n":
            end += 1
        existing = existing[:start] + existing[end:]
    match = _LEGACY_OPENING.search(existing)
    if match:
        existing = existing[:match.start()] + existing[match.end():]
    return existing


def _upsert_opening_fact(facts: dict, hook: str, ts: str) -> dict:
    """One plot_local KEY FACT for the offered hook; replace on re-run, never stack."""
    if not isinstance(facts, dict):
        facts = {}
    bucket = facts.get(_OPENING_FACT_CATEGORY)
    if not isinstance(bucket, list):
        bucket = []
    kept = []
    for item in bucket:
        txt = item.get("fact", "") if isinstance(item, dict) else str(item)
        if str(txt).startswith(_OPENING_FACT_PREFIX):
            continue
        kept.append(item)
    kept.append({"fact": f"{_OPENING_FACT_PREFIX} {hook}", "timestamp": ts})
    facts[_OPENING_FACT_CATEGORY] = kept
    return facts


def _commit_opening(cdir: Path, overview: dict, facts: dict, log_text: str) -> None:
    """Write overview + facts + session-log together. Partial write is the bug.

    plots.json is not rewritten — the seed no longer mutates plots. session-log
    is rewritten only so a fabricated opening-seed block is stripped; real
    sessions stay. An empty log after removal is fine.
    """
    ov_tmp = cdir / "campaign-overview.json.tmp"
    facts_tmp = cdir / "facts.json.tmp"
    log_tmp = cdir / "session-log.md.tmp"
    ov_tmp.write_text(json.dumps(overview, indent=2), encoding="utf-8")
    facts_tmp.write_text(json.dumps(facts, indent=2), encoding="utf-8")
    log_tmp.write_text(log_text, encoding="utf-8")
    ov_tmp.replace(cdir / "campaign-overview.json")
    facts_tmp.replace(cdir / "facts.json")
    log_tmp.replace(cdir / "session-log.md")


def _apply_opening(campaign_dir, character=None, timestamp=None, *, reseed=False) -> dict:
    cdir = Path(campaign_dir)
    ts = timestamp or _now()

    overview = _load(cdir, "campaign-overview.json")
    plots = _load(cdir, "plots.json")
    locations = _load(cdir, "locations.json")
    facts = _load(cdir, "facts.json")

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
    overview["opening_hook"] = {
        "location": opening_loc,
        "plot": chosen,
        "hook": hook,
    }
    if reseed:
        overview["opening_matched_to_pc"] = True

    facts = _upsert_opening_fact(facts, hook, ts)

    log_path = cdir / "session-log.md"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    log_text = _strip_opening_log(existing)

    _commit_opening(cdir, overview, facts, log_text)
    return {"seeded": True, "opening_location": opening_loc, "first_plot": chosen, "hook": hook}


def seed_opening(campaign_dir, timestamp=None) -> dict:
    """Provisional seed (import / new-game pipeline). Opens on spine[0] / first main."""
    return _apply_opening(campaign_dir, character=None, timestamp=timestamp, reseed=False)


def reseed_opening(campaign_dir, character, timestamp=None) -> dict:
    """Rewrite location + opening_hook (and the KEY FACT) once the PC exists.

    Atomic: starting location, offered hook, and the plot_local KEY FACT are
    computed then written together; a previously fabricated opening-seed
    session-log block is stripped. Plot statuses are left as they were — this
    does not start the chosen plot. Plot selection uses `_pick_opening_plot`
    (PC-aware when the arc has 2+ plots).
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
