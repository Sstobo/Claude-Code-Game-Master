---
type: Flow
title: Onboarding and the death hand-off
description: How a player enters a world in one question, and how the story continues after the PC dies rather than ending.
sources:
  - { resource: /lib/identity_onboarding.py }
  - { resource: /lib/player_manager.py }
  - { resource: /CLAUDE.md }
generated: { by: claude-fable-5, at: 2026-08-13T14:16:30Z }
verified: { by: claude-fable-5, at: 2026-08-13T15:15:27Z }
---

# Onboarding and the death hand-off

Two flows, one shared conviction: **the mechanics are not the point, and the player should
never be made to do bookkeeping to keep playing.** Entering a world costs one question;
dying costs one choice.

## Entry: three doors, one question

"Who are you in this world?" dispatches to three builders
(`lib/identity_onboarding.py:76`):

| Mode | Player supplies | Where the sheet comes from |
|---|---|---|
| `canon` | an NPC name | that NPC's `character_sheet` if present, plus their `context` as `voice` |
| `original` | a name + one-line concept | defaults; attributes left empty and inferred against the kit |
| `nameless` | nothing | defaults, named "A nameless traveler" |

All three produce the **open** shape internally, and `save_character` persists
`to_flat(char)`. The extra keys the builders add — `voice`, `origin`, `concept` — survive
the flattening as top-level fields, which is why `origin: "canon"` is still readable on a
live sheet. See [the player character sheet](../modules/player-character.md).

The full 9-step builder still exists as `/create-character`; this replaces it as the
*default*, not as the only path. The design bet: a player arrives with an "I love this
book" spike, and spending it on ability scores wastes it.

`_default_vitals()` returns a **fresh nested dict every call** — an explicit fix for
characters aliasing one another's HP, and the reason there's a regression test for it
(`tests/test_identity_onboarding.py:40`).

## Death: persist, narrate, then offer the hand-off

Order matters and is stated in `CLAUDE.md`: persist first, narrate second, menu third.
Offering the menu before the death has landed narratively is the failure mode this
ordering exists to prevent.

1. `gm-player.sh kill "<name>" --cause "<how>"` — sets `status: dead`, HP 0, stamps
   `died_at`. Log it as a fact; record any consequence it triggers.
2. Narrate the death with weight. **No menu yet.**
3. Offer three continuations: take over a **party member**, roll a **new character**, or
   step in as a **canon figure**. (Solo with no party and no fitting canon figure: options
   2 and 3 only.)
4. Swap, bridge the fiction, resume.

## `become()` is the only path that moves a sheet

`gm-player.sh become "<name>"` (`lib/player_manager.py:542`) does five things in one call:
resolves the name **alias-aware** (so "Princess Donut" finds "Donut"), flattens the party
member's `character_sheet` into `character.json`, archives the fallen PC to
`fallen/<name>-<id>.json`, updates `current_character` on the overview, and **demotes the
promoted NPC from the party** (`is_party_member: false`, `became_pc: true`) so they aren't
tracked twice. The NPC record itself stays — the world still knows who they were.

Its two hard preconditions are worth knowing before the moment arrives, because both fail
loudly mid-hand-off:

- the target must already be `is_party_member` — promote first (`gm-npc.sh promote`)
- the target must have a `character_sheet`

The new sheet gets `status: alive` and has `died_at` / `cause` stripped, so a sheet that
was previously killed can be taken over cleanly.

## Nothing is deleted

The fallen PC's sheet is archived, not removed; the dead status is a field, not an absence.
That is what lets the world keep referencing, mourning, looting, and avenging a dead hero —
the "the show goes on" framing in `CLAUDE.md` is backed by state that still exists.

## Related

- [The player character sheet](../modules/player-character.md)
- [NPC model](../modules/npc-model.md) — where party sheets live before the swap
- [Two validate_character functions](../gotchas/identity-onboarding-schema-drift.md)
