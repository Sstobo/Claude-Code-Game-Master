#!/usr/bin/env python3
"""Collapse the legacy npc.location_tags field into canonical tags.locations.

Two spellings of "where is this NPC" drifted for months: extraction wrote a flat
`location_tags` list, the runtime read `tags.locations`, and the conversion
happened only at NPC-creation time — so import passes that fixed one field left
the other stale, and an NPC tagged only the legacy way was invisible to scene
presence and on_npc triggers. This makes `tags.locations` the ONLY field:
legacy values are merged in (case-insensitive dedupe, first casing wins) and
`location_tags` is deleted.

Runs at import normalize (so every downstream pass sees one field) and on
demand for existing campaigns via `gm-npc.sh unify-tags`.
"""

from typing import Any, Dict


def unify_location_tags(npcs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge each NPC's location_tags into tags.locations and delete the legacy
    field. Mutates in place. Returns {"migrated": [names], "tags_added": n}."""
    report = {"migrated": [], "tags_added": 0}
    for name, npc in (npcs or {}).items():
        if not isinstance(npc, dict) or "location_tags" not in npc:
            continue
        legacy = npc.pop("location_tags") or []
        tags = npc.get("tags")
        if not isinstance(tags, dict):
            tags = {"locations": [], "quests": []}
            npc["tags"] = tags
        locs = tags.setdefault("locations", [])
        seen = {str(x).strip().lower() for x in locs}
        for t in legacy:
            key = str(t).strip().lower()
            if key and key not in seen:
                locs.append(t)
                seen.add(key)
                report["tags_added"] += 1
        report["migrated"].append(name)
    return report
