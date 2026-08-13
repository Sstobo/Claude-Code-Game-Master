---
type: Gotcha
title: An NPC's location lives in two fields
description: Import passes fix `location_tags`; the runtime reads `tags.locations`. The mapping happens once, at creation — so patch both when you move someone.
sources:
  - { resource: /lib/npc_manager.py }
  - { resource: /lib/search.py }
  - { resource: /lib/integrity_gate.py }
  - { resource: /lib/location_reconcile.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# An NPC's location lives in two fields

Two spellings, two halves of the system, one conversion point.

| Field | Shape | Used by |
|---|---|---|
| `location_tags` | flat list on the NPC | extraction schema, `minor_stubs`, `location_reconcile`, `integrity_gate` |
| `tags.locations` | nested under `tags` | every runtime read: `search_npcs_by_tag`, the session brief, consequence presence |

**The conversion happens only when the NPC record is built** — `lib/npc_manager.py:784` and
`lib/agent_extractor.py:428` both map `location_tags` → `tags['locations']` at creation
time. Nothing re-syncs them afterward.

So an import pass that canonicalizes `location_tags` (which is what
`integrity_gate` and `location_reconcile` do) does **not** update `tags.locations` on an
NPC record that already exists. And an NPC that only ever carried `location_tags` is
invisible to "who is present" — it will not appear in the scene brief and will not fire
`on_npc` consequences.

**The rule: when you move an NPC, write both fields.** `gm-npc.sh tag-location` writes the
runtime one; the import-side field needs patching separately if it is present.

To check a live campaign rather than trusting this:

```bash
uv run python -c "
import json,sys; d=json.load(open(sys.argv[1]))
print('tags.locations:', sum(1 for v in d.values() if isinstance(v,dict) and v.get('tags',{}).get('locations')))
print('location_tags :', sum(1 for v in d.values() if isinstance(v,dict) and v.get('location_tags')))
" "$(bash tools/gm-campaign.sh path)/npcs.json"
```

## Matching is substring, case-insensitive — and duplicates are common

`search_npcs_by_tag` lowercases both sides and tests `tag_lower in t.lower()`
(`lib/search.py:90`). That is forgiving of case and of a location name that is a prefix of
another, but it also means a tag list routinely holds the same place twice in different
casings — the shipped fixture campaign has an NPC tagged both `Tutorial Guild Hall` and
`tutorial-guild-hall`. Harmless for presence checks; misleading if you count tags.

Note the field is spelled inconsistently *within* the runtime side too: the method accepts
`location` or `locations` and normalizes (`lib/search.py:76`).

## Related

- [NPC model](../modules/npc-model.md)
- [Entity graph](../modules/entity-graph.md) — the alias resolver that handles the *name* half of this problem
