#!/usr/bin/env python3
"""Reconcile referenced-but-missing locations before the integrity gate.

Plots, NPC location_tags, and location connections reference places that were
never extracted as nodes (e.g. stairwell stations 24/36/48/72). This pass, for
every location reference that does not resolve to a real key via the alias
resolver (including a descriptive phrasing that normalizes onto an existing
node — those are aliased onto that node, not stubbed), STUBS it: a lightweight node with a source passage, a bidirectional
connection to the most-connected hub, and `low_confidence: true` — the flag says
"the book named this place, nobody has verified what it is", which is a judgment
the GM can make in play and a shape heuristic cannot.

The old heuristic (drop anything with a slash, the word "unknown", or more than
six words) deleted real places from the world to protect a machine gate. What is
still dropped depends on where the reference came from:

  - a **connection target** may be a routing rule rather than a destination
    ("Transfer stations ending in 1", "Any line") — `connection_normalize`'s test
    for that runs here too, on its home ground;
  - a **plot or tag reference** names a place the book put someone in, so only a
    blank is dropped. "The Upper Level of the Tower of the Elephant" and
    "Kandahar via the Zhaibar Pass" are places, and a phrase test applied to them
    deletes real geography.

Dropped names are persisted as facts rather than printed and lost.

Runs after cap, before the integrity gate's strict fail check.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from connection_normalize import _is_rule_phrase
from entity_aliases import reuse_existing_key


def _add_alias(entity: dict, variant: str):
    if not isinstance(entity, dict):
        return
    aliases = entity.setdefault("aliases", [])
    if variant not in aliases:
        aliases.append(variant)


def _is_stubbable(name: str, is_connection: bool = False) -> bool:
    """False only for what names no place at all.

    Blanks never name a place. Routing rule-prose only fails as a CONNECTION
    target — that is the shape `connection_normalize` was written against. The
    same test on a plot or tag reference throws away real geography, so when in
    doubt the answer is a low-confidence stub, not a deletion.
    """
    if not name or len(name.strip()) < 2:
        return False
    if is_connection and _is_rule_phrase(name):
        return False
    return True


def _hub_name(locations: dict):
    """Most-connected existing location, used as the anchor for stubs."""
    best, best_deg = None, -1
    for name, loc in locations.items():
        if not isinstance(loc, dict):
            continue
        deg = len(loc.get("connections", []) or [])
        if deg > best_deg:
            best, best_deg = name, deg
    return best


def _make_stub(name: str, hub: str, passage: str = "") -> dict:
    stub = {
        "name": name,
        "position": "",
        "description": passage or f"(Auto-stubbed location referenced by the source but not extracted as a full node.)",
        "connections": [],
        "features": [],
        "inhabitants": [],
        "hazards": [],
        "notes": "auto-stub: created by missing-location-reconcile",
        "source": "auto-stub",
        "low_confidence": True,
    }
    if hub:
        stub["connections"].append({"to": hub, "path": "(auto-linked; refine in play)"})
    if passage:
        stub["context"] = [passage]
    return stub


def reconcile(npcs: dict, locations: dict, plots: dict, passage_fn=None) -> dict:
    """Stub or drop unresolved location references in place. Returns a report.

    passage_fn: optional callable(name)->str returning a source passage for a stub.
    """
    report = {"stubbed": [], "dropped": [], "kept": 0}
    hub = _hub_name(locations)

    def ensure(name, is_connection=False):
        """Return a real key for `name`, creating a stub if needed; None if dropped."""
        key = reuse_existing_key(name, locations)
        if key:
            report["kept"] += 1
            if name != key:
                _add_alias(locations[key], name)
            return key
        if _is_stubbable(name, is_connection):
            passage = ""
            if passage_fn:
                try:
                    passage = passage_fn(name) or ""
                except Exception:
                    passage = ""
            locations[name] = _make_stub(name, hub, passage)
            # bidirectional: hub points back at the stub
            if hub and isinstance(locations.get(hub), dict):
                conns = locations[hub].setdefault("connections", [])
                if not any(isinstance(c, dict) and c.get("to") == name for c in conns):
                    conns.append({"to": name, "path": "(auto-linked; refine in play)"})
            report["stubbed"].append(name)
            return name
        report["dropped"].append(name)
        return None

    # plot.locations
    for plot in (plots or {}).values():
        if isinstance(plot, dict) and "locations" in plot:
            plot["locations"] = [k for k in (ensure(r) for r in plot["locations"]) if k]

    # npc location tags — canonical tags.locations (legacy location_tags handled
    # too, for campaigns predating tag unification).
    for npc in (npcs or {}).values():
        if not isinstance(npc, dict):
            continue
        tags = npc.get("tags")
        if isinstance(tags, dict) and "locations" in tags:
            tags["locations"] = [k for k in (ensure(t) for t in tags["locations"]) if k]
        if "location_tags" in npc:
            npc["location_tags"] = [k for k in (ensure(t) for t in npc["location_tags"]) if k]

    # location.connections[].to  (iterate over a snapshot of names; stubs may be added)
    for lname in list(locations.keys()):
        loc = locations[lname]
        if not isinstance(loc, dict):
            continue
        new_conns = []
        for conn in loc.get("connections", []) or []:
            if isinstance(conn, dict) and "to" in conn:
                key = ensure(conn["to"], is_connection=True)
                if key:
                    conn["to"] = key
                    new_conns.append(conn)
                # dropped target -> drop the dead edge
            else:
                new_conns.append(conn)
        loc["connections"] = new_conns

    return report


FACT_CATEGORY = "dropped_references"


def _persist_dropped(cdir: Path, dropped: list):
    """Record dropped references as campaign facts, not stdout the import loses.

    facts.json shape ({category: [{fact, timestamp}]}) is written directly —
    NoteManager needs an active campaign, and reconcile only has a directory.
    """
    if not dropped:
        return
    path = cdir / "facts.json"
    facts = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(facts, dict):
        return
    bucket = facts.setdefault(FACT_CATEGORY, [])
    known = {f.get("fact") for f in bucket if isinstance(f, dict)}
    stamp = datetime.now(timezone.utc).isoformat()
    for name in dropped:
        fact = (f"Import dropped a location reference that named no destination: "
                f"'{name}' (a connection routing rule, or blank).")
        if fact not in known:
            bucket.append({"fact": fact, "timestamp": stamp})
            known.add(fact)
    path.write_text(json.dumps(facts, indent=2))


def run_reconcile(campaign_dir) -> dict:
    cdir = Path(campaign_dir)

    def _load(name):
        p = cdir / name
        return json.loads(p.read_text()) if p.exists() else {}

    npcs, locations, plots = _load("npcs.json"), _load("locations.json"), _load("plots.json")

    # Optional RAG passage lookup for stub descriptions.
    passage_fn = None
    try:
        from entity_enhancer import EntityEnhancer
        enh = EntityEnhancer()
        if enh._ensure_rag():
            def passage_fn(name):
                hits = enh.search_raw(name, n_results=1)
                return hits[0]["text"][:500] if hits else ""
    except Exception:
        passage_fn = None

    report = reconcile(npcs, locations, plots, passage_fn=passage_fn)
    _persist_dropped(cdir, report["dropped"])

    if locations:
        (cdir / "locations.json").write_text(json.dumps(locations, indent=2))
    if npcs:
        (cdir / "npcs.json").write_text(json.dumps(npcs, indent=2))
    if plots:
        (cdir / "plots.json").write_text(json.dumps(plots, indent=2))
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reconcile missing locations")
    parser.add_argument("campaign_dir")
    args = parser.parse_args()
    report = run_reconcile(args.campaign_dir)
    print(f"  stubbed: {len(report['stubbed'])}  {report['stubbed'][:8]}")
    print(f"  dropped: {len(report['dropped'])}  {report['dropped'][:8]}")
    print(f"  resolved (kept): {report['kept']}")


if __name__ == "__main__":
    main()
