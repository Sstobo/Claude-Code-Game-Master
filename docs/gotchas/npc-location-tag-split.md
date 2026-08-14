---
type: Gotcha
title: An NPC's location lived in two fields (unified 2026-08-13)
description: tags.locations is now the only location field — but pre-unification campaigns still carry the legacy split and need a one-time migration.
sources:
  - { resource: /lib/tag_unify.py }
  - { resource: /lib/npc_manager.py }
  - { resource: /lib/search.py }
  - { resource: /lib/entity_manager.py }
generated: { by: cursor-grok-4.6, at: 2026-08-14T19:59:23Z }
---

# An NPC's location lived in two fields (unified 2026-08-13)

From the first imports until 2026-08-13, "where is this NPC" had two spellings:
extraction wrote a flat `location_tags`, the runtime read `tags.locations`, and the
conversion happened only at NPC creation — so import passes that canonicalized one field
left the other stale, and an NPC tagged only the legacy way was invisible to scene
presence and `on_npc` triggers. The world read emptier than its data.

**Now `tags.locations` is the only field.** `lib/tag_unify.py` merges the legacy list in
(case-insensitive dedupe) and deletes it; import runs it inside `normalize`, so every
downstream pass and the whole runtime see one field. `location_tags` survives only as the
extraction agents' *output* spelling, converted at the normalize boundary — consistent
with [extraction schema ≠ runtime schema](extraction-vs-runtime-schema.md).

## The part that still bites: old campaigns

A campaign imported before the unification still carries the split on disk. Nothing
migrates it automatically — run the one-time migration:

```bash
bash tools/gm-npc.sh unify-tags
```

Idempotent; prints what it merged. If an NPC in an old campaign never shows up in scenes,
run this before debugging anything else. (`integrity_gate` and `location_reconcile` still
handle the legacy field defensively for exactly these campaigns.)

## Matching: presence is exact; search-by-tag is substring

Presence (`npcs_present` in `lib/entity_manager.py`) is case-insensitive **equality**
of the current location against a `tags.locations` entry (or `is_party_member`).
"The Inn" does not match "The Inner Sanctum". That used to be substring, which is
why the place brief and the session brief could disagree on who was in the room.

CLI `gm-search.sh --tag-location` / `--tag-quest` still uses substring containment
(`search_npcs_by_tag`) as a discovery search. That is not the scene-presence path.
Tag lists can still hold near-duplicate spellings (`Tutorial Guild Hall` /
`tutorial-guild-hall`); harmless for exact presence, noisy if you count search hits.

## Related

- [NPC model](../modules/npc-model.md)
- [Entity graph](../modules/entity-graph.md) — the alias resolver that handles the *name* half of this problem
