---
slug: key-facts-reads-choices
title: KEY FACTS reads the player_choices and npc_relations categories it advertises
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: make-the-world-remember
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: KEY_FACT_CATEGORIES adds player_choices, npc_relations and lore; per-category depth 4 -> 3. session_events and rules stay out by design and remain reachable through recall, so no advertised category is a write-only hole.
reviewRounds: null
implementer: claude-fable-5
createdAt: 2026-08-14T02:25:26Z
updatedAt: 2026-08-14T02:25:26Z
---

## Parent

Make the World Remember (prds/make-the-world-remember.md)

## Category

bug

## What to build

`tools/gm-note.sh:11` advertises six fact categories to the GM, including `player_choices`
and `npc_relations`. `_key_facts` (`lib/session_manager.py:812-827`) reads exactly three:
`plot_local`, `plot_regional`, `plot_world`. So the two categories that most naturally hold
"what the player decided" and "how this NPC stands with the party" are write-only — the GM
is told to file them and nothing ever reads them back.

Add `player_choices` and `npc_relations` to the category tuple at `:818`.

Keep the existing per-category bound (`items[-per_category:]`, default 4) so the block does
not balloon; with five categories the worst case is 20 lines, which is in line with the
other bounded blocks. If that reads as too much in practice, prefer lowering
`per_category` over dropping a category.

Consider whether `lore` and `rules` (also advertised at `gm-note.sh:11`) belong here too —
argue it either way in the resolution, but do not silently leave them in the same hole:
either read them or narrow the tool's help text so it stops promising a home that does not
exist.

## Acceptance criteria

- A fact filed with `gm-note.sh add player_choices "..."` appears in the KEY FACTS block of
  `gm-session.sh context`.
- Same for `npc_relations`.
- The three `plot_*` categories are unaffected in content and order.
- Every category `gm-note.sh` advertises is either read by context or no longer advertised.
- `docs/modules/scene-context.md` updated and restamped if its description of KEY FACTS
  changes.
