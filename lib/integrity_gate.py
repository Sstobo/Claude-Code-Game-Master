#!/usr/bin/env python3
"""Post-extraction integrity gate: canonicalize cross-references, fail on unresolved.

Extracted files cross-reference each other by NAME (plot.npcs, plot.locations,
npc.location_tags, location.connections[].to). Naming drift makes those links break
at runtime. This pass resolves every reference to a real entity key via the shared
alias resolver, rewrites the reference to the canonical key, and records the variant
as an `aliases` entry on the target. Anything still unresolved is reported; near-duplicate
keys (two existing keys that normalize equal) are reported as findings. In strict
mode the gate exits non-zero so a broken import is caught, not shipped.

Run AFTER cap and (when present) AFTER missing-location reconciliation, which can
create stub nodes that satisfy otherwise-unresolved location references.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import normalize_entity_name, resolve_entity_name


def _add_alias(entity: dict, variant: str):
    if not isinstance(entity, dict):
        return
    aliases = entity.setdefault("aliases", [])
    if variant not in aliases:
        aliases.append(variant)


def _resolve_list(refs, target_entities, owner_kind, owner_name, report):
    """Resolve+rewrite a list of name references against target_entities (dict).

    Mutates `refs` in place to canonical keys. Records rewrites/aliases/unresolved.
    Returns the rewritten list.
    """
    out = []
    for ref in refs or []:
        if ref in target_entities:
            out.append(ref)
            continue
        key = resolve_entity_name(ref, target_entities)
        if key:
            out.append(key)
            report["rewritten"].append({"owner": f"{owner_kind}:{owner_name}", "from": ref, "to": key})
            _add_alias(target_entities[key], ref)
            report["aliased"].append({"entity": key, "alias": ref})
        else:
            out.append(ref)  # leave as-is; flagged unresolved
            report["unresolved"].append({"owner": f"{owner_kind}:{owner_name}", "ref": ref, "kind": owner_kind})
    return out


def _near_duplicate_keys(entities: dict, kind: str) -> list:
    """Groups of keys that normalize equal — each is a valid target for itself."""
    buckets = {}
    for k in entities or {}:
        n = normalize_entity_name(k)
        if not n:
            continue
        buckets.setdefault(n, []).append(k)
    return [
        {"kind": kind, "normalized": n, "keys": keys}
        for n, keys in buckets.items()
        if len(keys) > 1
    ]


def canonicalize(npcs: dict, locations: dict, plots: dict) -> dict:
    """Canonicalize all cross-references in place. Returns a report dict."""
    report = {"rewritten": [], "aliased": [], "unresolved": [], "near_duplicates": []}

    for pname, plot in (plots or {}).items():
        if not isinstance(plot, dict):
            continue
        if "npcs" in plot:
            plot["npcs"] = _resolve_list(plot["npcs"], npcs, "plot.npcs", pname, report)
        if "locations" in plot:
            plot["locations"] = _resolve_list(plot["locations"], locations, "plot.loc", pname, report)

    for nname, npc in (npcs or {}).items():
        if not isinstance(npc, dict):
            continue
        tags = npc.get("tags")
        if isinstance(tags, dict) and "locations" in tags:
            tags["locations"] = _resolve_list(tags["locations"], locations, "npc.tag", nname, report)
        if "location_tags" in npc:  # legacy, pre-unification campaigns
            npc["location_tags"] = _resolve_list(npc["location_tags"], locations, "npc.tag", nname, report)

    for lname, loc in (locations or {}).items():
        if not isinstance(loc, dict):
            continue
        for conn in loc.get("connections", []) or []:
            if isinstance(conn, dict) and "to" in conn:
                resolved = _resolve_list([conn["to"]], locations, "loc.conn", lname, report)
                conn["to"] = resolved[0]

    report["near_duplicates"] = (
        _near_duplicate_keys(npcs, "npc")
        + _near_duplicate_keys(locations, "location")
        + _near_duplicate_keys(plots, "plot")
    )
    return report


def run_gate(campaign_dir, strict: bool = True) -> dict:
    """Canonicalize the campaign's cross-refs in place and report.

    Returns the report. If strict and any reference is unresolved or any
    near-duplicate keys exist, raises SystemExit(1) after writing the report
    (so callers/CI see the failure).
    """
    cdir = Path(campaign_dir)

    def _load(name):
        p = cdir / name
        return json.loads(p.read_text()) if p.exists() else {}

    npcs, locations, plots = _load("npcs.json"), _load("locations.json"), _load("plots.json")
    report = canonicalize(npcs, locations, plots)

    if npcs:
        (cdir / "npcs.json").write_text(json.dumps(npcs, indent=2))
    if locations:
        (cdir / "locations.json").write_text(json.dumps(locations, indent=2))
    if plots:
        (cdir / "plots.json").write_text(json.dumps(plots, indent=2))

    if strict and (report["unresolved"] or report["near_duplicates"]):
        if report["unresolved"]:
            sys.stderr.write(f"INTEGRITY GATE FAILED: {len(report['unresolved'])} unresolved reference(s):\n")
            for u in report["unresolved"]:
                sys.stderr.write(f"  {u['owner']} -> '{u['ref']}'\n")
        if report["near_duplicates"]:
            sys.stderr.write(
                f"INTEGRITY GATE FAILED: {len(report['near_duplicates'])} near-duplicate key group(s):\n"
            )
            for d in report["near_duplicates"]:
                sys.stderr.write(f"  {d['kind']}: {d['keys']}\n")
        raise SystemExit(1)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Post-extraction integrity gate")
    parser.add_argument("campaign_dir")
    parser.add_argument("--no-strict", action="store_true", help="report only, do not fail on unresolved")
    args = parser.parse_args()
    report = run_gate(args.campaign_dir, strict=not args.no_strict)
    print(f"  rewritten:  {len(report['rewritten'])}")
    print(f"  aliased:    {len(report['aliased'])}")
    print(f"  unresolved: {len(report['unresolved'])}")
    print(f"  near-dupes: {len(report['near_duplicates'])}")


if __name__ == "__main__":
    main()
