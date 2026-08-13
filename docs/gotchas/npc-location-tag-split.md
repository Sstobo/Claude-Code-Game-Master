---
type: Gotcha
title: An NPC's location lived in two fields (unified 2026-08-13)
description: tags.locations is now the only location field — but pre-unification campaigns still carry the legacy split and need a one-time migration.
sources:
  - { resource: /lib/tag_unify.py }
  - { resource: /lib/npc_manager.py }
  - { resource: /lib/search.py }
generated: { by: claude-fable-5, at: 2026-08-13T14:46:10Z }
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

## Matching is substring, case-insensitive

`search_npcs_by_tag` lowercases both sides and tests containment (`lib/search.py:90`) —
forgiving of case and of a location name that prefixes another. Tag lists can still hold
near-duplicate spellings (`Tutorial Guild Hall` / `tutorial-guild-hall`); harmless for
presence, misleading if you count tags.

## Related

- [NPC model](../modules/npc-model.md)
- [Entity graph](../modules/entity-graph.md) — the alias resolver that handles the *name* half of this problem
