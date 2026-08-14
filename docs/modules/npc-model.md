---
type: Module
title: The NPC model
description: What an NPC carries beyond a description — inner life, canonical voice lines, party-member sheets, and proxy combat stats.
sources:
  - { resource: /lib/npc_manager.py }
  - { resource: /lib/npc_stats.py }
generated: { by: gk-a8r14q, at: 2026-08-14T18:00:37Z }
verified: { by: claude-fable-5, at: 2026-08-13T14:16:30Z }
---

# The NPC model

An NPC in `npcs.json` is four things stacked on one key: a description, an **inner life**,
a **voice**, and — if promoted — a full **character sheet**. The stacking is additive by
design, so an NPC extracted from a book with nothing but a name still loads.

## `voice` and `context` are not the same field

This trips people every time:

| Field | Holds | Read by |
|---|---|---|
| `context` | **canonical voice lines** — verbatim dialogue from the source | `get_voice()` (`lib/npc_manager.py:274`) |
| `voice` | a free-text *description* of how they speak | `get_inner_life()` |

So "set the NPC's voice" is ambiguous: `set-inner` writes the description, while the
quotable lines live in `context`, which the RAG enhancement pass populates.
The session brief prints lines from `context` under the heading "NPC VOICES", so an NPC
with a rich `voice` description but an empty `context` speaks no lines at all.

`get_voice` is explicitly read-only and never mutates `context` — enhancement writes it,
play only reads it.

## Inner life defaults, and only the secret's existence leaks

`INNER_LIFE_FIELDS = ('goal', 'secret', 'current_mood', 'voice', 'bonds')`, all optional,
all defaulted on read (`current_mood` → `'neutral'`). `current_mood` persists across
sessions — an NPC you angered stays angry.

The `secret` field is surfaced to the model as **existence only**: the session brief prints
`"has a secret"` and never the text. See [scene context](scene-context.md).

## Party members carry a second sheet, in a different shape

Promote copies existing combat stats into the party sheet when the NPC has them
(the stat-npcs proxy or a monster-manual lookup); defaults apply only to a
genuinely statless NPC, and the output says which. Note what this is **not**: it is a
nested sheet on the NPC record, not the flat top-level shape the PC uses
(see [player character](player-character.md)). The two never converge except in
`gm-player.sh become`, which copies a party sheet into `character.json` and flattens it.

`demote_from_party_member` keeps the `character_sheet` — history is preserved, only the
flag flips. Party membership is also what makes an NPC count as *present* everywhere,
regardless of location tags (`lib/consequence_manager.py:263`).

## Proxy stats are difficulty tiers, not statblocks

Extracted NPCs arrive with null `ac`/`hp`/`cr`, so `npc_stats.enrich` assigns one of three
coarse tiers — boss (hp 120 / cr 8), standard (hp 45 / cr 3), minion (hp 18 / cr 1) — and
flags non-combatants `statless: True`.

`statless` is meaningfully different from "no stats yet": it records the judgment that this
character should never be rolled against. Treat a statless NPC as a scene, not an
encounter; treat a tier as a difficulty dial to adjust in the moment, never as a canonical
statblock. For a real statblock in a D&D-kit campaign, the `monster-manual` agent is the
authority.

## Location tags: one field, since 2026-08-13

`tags.locations` is the only location field — the legacy `location_tags` split was
unified (`lib/tag_unify.py`, run at import normalize). Campaigns imported before then
need the one-time `gm-npc.sh unify-tags`; see
[the tag-split gotcha](../gotchas/npc-location-tag-split.md).

## Related

- [Entity graph](entity-graph.md) — how NPC names resolve despite drift
- [RAG stack](rag-stack.md) — what fills `context` with real dialogue
