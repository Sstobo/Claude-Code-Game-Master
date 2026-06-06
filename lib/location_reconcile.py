#!/usr/bin/env python3
"""Reconcile referenced-but-missing locations before the integrity gate.

Plots, NPC location_tags, and location connections reference places that were
never extracted as nodes (e.g. stairwell stations 24/36/48/72) or were dropped by
the cap. This pass, for every location reference that does not resolve to a real
key via the alias resolver:
  - STUB it (create a lightweight node with a source passage + a bidirectional
    connection to the most-connected hub) when the name looks like a real place; or
  - DROP the reference (and report it) when it is a one-off descriptive phrase
    ("location unknown", slashes, long prose).

Runs after cap, before the integrity gate's strict fail check.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import resolve_entity_name


def _is_stubbable(name: str) -> bool:
    """A real-place name vs a descriptive phrase. Conservative."""
    if not name or len(name.strip()) < 2:
        return False
    low = name.lower()
    if "unknown" in low or "/" in name:
        return False
    if len(name.split()) > 6:
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

    def ensure(name):
        """Return a real key for `name`, creating a stub if needed; None if dropped."""
        key = resolve_entity_name(name, locations)
        if key:
            report["kept"] += 1
            return key
        if _is_stubbable(name):
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

    # npc.location_tags
    for npc in (npcs or {}).values():
        if isinstance(npc, dict) and "location_tags" in npc:
            npc["location_tags"] = [k for k in (ensure(t) for t in npc["location_tags"]) if k]

    # location.connections[].to  (iterate over a snapshot of names; stubs may be added)
    for lname in list(locations.keys()):
        loc = locations[lname]
        if not isinstance(loc, dict):
            continue
        new_conns = []
        for conn in loc.get("connections", []) or []:
            if isinstance(conn, dict) and "to" in conn:
                key = ensure(conn["to"])
                if key:
                    conn["to"] = key
                    new_conns.append(conn)
                # dropped target -> drop the dead edge
            else:
                new_conns.append(conn)
        loc["connections"] = new_conns

    return report


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
