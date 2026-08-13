#!/usr/bin/env python3
"""Extraction shape normalization; stub plot-referenced NPCs that the cap dropped.

The hard 30-cap can drop NPCs that plots still reference (when >30 are referenced),
leaving plot.npcs links that don't resolve. This creates a minimal NPC stub for each
such reference (a generic, monster-manual-statveable placeholder) and rewrites the
reference to the stub key — so the strict integrity gate passes. Also validates
plot `type` against the canonical enum (`schemas.PLOT_TYPES`), mapping known
synonyms and falling back to 'side' — with a warning — for anything unknown.

Run after cap + integrity-canonicalize, alongside missing-location-reconcile.

Also home to the ONE shape rule the import gate and `normalize` share
(`normalize_entity_shape`): EXTRACTION_RESULT_SCHEMA declares keyed dicts, but
extractor agents drift to list-shaped output in practice (the conan import's
items.json was a 43-element list), and every runtime manager expects a keyed
{name: {...}} dict — so lists, keyed dicts, and wrapper dicts all have to land
as the same flat shape. Counting one shape only is how a correct 43-item
extraction used to report "EMPTY (0 entities)".
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import resolve_entity_name
from schemas import PLOT_TYPES

# The four extraction types, and the wrapper key an agent may nest its list/dict
# under (plots.json wraps as "plot_hooks", per EXTRACTION_RESULT_SCHEMA).
EXTRACTION_TYPES = ("npcs", "locations", "items", "plots")
WRAPPER_KEYS = {"npcs": "npcs", "locations": "locations", "items": "items", "plots": "plot_hooks"}

# A book with no treasure or no explicit quest hooks is still playable; a book
# with no cast or nowhere to stand is a failed extraction. Empty items/plots warn.
REQUIRED_NONEMPTY = ("npcs", "locations")


def _unwrap(data, type_name: str):
    """Return the entity container (list or keyed dict) inside an agent's file.

    Unwraps the type's wrapper key only when it is a GENUINE wrapper: it holds a
    list, or it stands alone beside non-entity scraps (`document`, `metadata`). A
    file whose other values are entities is already flat — unwrapping it would
    swallow the whole file for the sake of an entity named "items".
    """
    key = WRAPPER_KEYS.get(type_name, type_name)
    if isinstance(data, dict):
        inner = data.get(key)
        if isinstance(inner, list):
            return inner
        siblings_are_entities = any(
            k != key and isinstance(v, dict) and "name" in v for k, v in data.items()
        )
        if isinstance(inner, dict) and not siblings_are_entities:
            return inner
    if isinstance(data, (list, dict)):
        return data
    raise ValueError(f"{type_name}: file holds {type(data).__name__}, expected a list or an object")


def _entity_pairs(data, type_name: str) -> list:
    """(name, entity) pairs from any extractor shape. Raises ValueError, naming the
    type and the offending entry, rather than letting a bad entity crash a caller."""
    container = _unwrap(data, type_name)
    if isinstance(container, dict):
        # Drop the document/extraction_date scraps agents leave beside entities.
        return [(k, v) for k, v in container.items() if isinstance(v, dict)]

    pairs = []
    for i, entity in enumerate(container):
        if not isinstance(entity, dict):
            raise ValueError(f"{type_name}: entry {i} is {type(entity).__name__}, expected an object")
        name = entity.get("name")
        if name is not None and not isinstance(name, str):
            raise ValueError(f"{type_name}: name is not a string (entry {i} is {type(name).__name__})")
        pairs.append((name or f"unnamed_{i}", entity))
    return pairs


def normalize_entity_shape(data, type_name: str) -> dict:
    """Return extractor output for one type in the flat {name: {...}} runtime shape.

    Accepts every shape an extractor agent produces: a bare list (real agent
    drift, seen in the wild), a bare keyed dict (what EXTRACTION_RESULT_SCHEMA
    declares), or either of those nested
    under the type's wrapper key beside stray document/metadata keys. Entities
    sharing a name collapse onto one key — `entry_count` reports the difference.
    """
    return dict(_entity_pairs(data, type_name))


def entry_count(data, type_name: str) -> int:
    """How many entities the agent WROTE, before same-name entries collapse."""
    return len(_entity_pairs(data, type_name))


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
