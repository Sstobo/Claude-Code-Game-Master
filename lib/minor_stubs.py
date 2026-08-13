#!/usr/bin/env python3
"""Stub plot-referenced NPCs that the cap dropped; validate plot taxonomy.

The hard 30-cap can drop NPCs that plots still reference (when >30 are referenced),
leaving plot.npcs links that don't resolve. This creates a minimal NPC stub for each
such reference (a generic, monster-manual-statveable placeholder) and rewrites the
reference to the stub key — so the strict integrity gate passes. Also validates
plot `type` against the canonical enum (`schemas.PLOT_TYPES`), mapping known
synonyms and falling back to 'side' — with a warning — for anything unknown.

Run after cap + integrity-canonicalize, alongside missing-location-reconcile.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import resolve_entity_name
from schemas import PLOT_TYPES

# Extractor vocabulary (see .claude/agents/extractor-plots.md) that isn't itself a
# canonical type but maps cleanly onto one. Anything outside both sets is unknown.
PLOT_TYPE_SYNONYMS = {
    "quest": "side",
    "side quest": "side",
    "faction quest": "side",
    "encounter": "side",
    "random encounter": "side",
    "mysteries": "mystery",
    "main quest": "main",
    "arc": "main",
    "plot point": "main",
    "turning point": "main",
    "conflict": "threat",
    "danger": "threat",
    "beat": "scene",
    "sequence": "scene",
    "plan": "idea",
    "concept": "idea",
}


def _make_npc_stub(name: str, referenced_by: str) -> dict:
    return {
        "name": name,
        "description": f"(Auto-stubbed minor character/threat referenced by '{referenced_by}' "
                       f"but not in the top-cap cast. Spawn monster-manual/npc-builder to flesh out.)",
        "attitude": "neutral",
        "tags": {"locations": [], "quests": []},
        "events": [],
        "stats": {},
        "dialogue": [],
        "source": "auto-stub",
    }


def stub_missing_npcs(npcs: dict, plots: dict) -> dict:
    """Stub unresolved plot.npcs refs and rewrite them to canonical keys."""
    report = {"stubbed": [], "kept": 0}
    for pname, plot in (plots or {}).items():
        if not isinstance(plot, dict) or "npcs" not in plot:
            continue
        new_refs = []
        for ref in plot.get("npcs", []) or []:
            key = resolve_entity_name(ref, npcs)
            if key:
                new_refs.append(key)
                report["kept"] += 1
            else:
                npcs[ref] = _make_npc_stub(ref, pname)
                new_refs.append(ref)
                report["stubbed"].append(ref)
        plot["npcs"] = new_refs
    return report


def validate_plot_types(plots: dict) -> dict:
    """Map plot types onto the canonical enum. Returns a report.

    Canonical types pass through untouched; known extractor synonyms map to their
    canonical type; anything else falls back to 'side' with a warning naming the
    original value (silent flattening used to erase threat/mystery from imports).
    """
    report = {"reclassified": []}
    for pname, plot in (plots or {}).items():
        if not isinstance(plot, dict):
            continue
        t = str(plot.get("type", "")).strip().lower()
        if t in PLOT_TYPES:
            continue
        mapped = PLOT_TYPE_SYNONYMS.get(t)
        if mapped is None:
            mapped = "side"
            print(f"[WARNING] Plot '{pname}': unknown type '{t or '(blank)'}' -> 'side'",
                  file=sys.stderr)
        plot["type"] = mapped
        report["reclassified"].append({"plot": pname, "from": t or "(blank)", "to": mapped})
    return report


def run_stubs(campaign_dir) -> dict:
    cdir = Path(campaign_dir)

    def _load(name):
        p = cdir / name
        return json.loads(p.read_text()) if p.exists() else {}

    npcs, plots = _load("npcs.json"), _load("plots.json")
    npc_report = stub_missing_npcs(npcs, plots)
    tax_report = validate_plot_types(plots)
    if npcs:
        (cdir / "npcs.json").write_text(json.dumps(npcs, indent=2))
    if plots:
        (cdir / "plots.json").write_text(json.dumps(plots, indent=2))
    return {**npc_report, **tax_report}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stub missing NPC refs + validate plot taxonomy")
    parser.add_argument("campaign_dir")
    args = parser.parse_args()
    r = run_stubs(args.campaign_dir)
    print(f"  npc stubs: {len(r['stubbed'])}  {sorted(set(r['stubbed']))[:8]}")
    print(f"  plot types reclassified: {len(r['reclassified'])}")


if __name__ == "__main__":
    main()
