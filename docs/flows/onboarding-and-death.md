---
type: Flow
title: Onboarding and the death hand-off
description: The holodeck door — one question, then the room — and how the story continues after the PC dies rather than ending.
sources:
  - { resource: /lib/identity_onboarding.py }
  - { resource: /tools/gm-player.sh }
  - { resource: /lib/player_manager.py }
  - { resource: /lib/opening_seed.py }
  - { resource: /CLAUDE.md }
  - { resource: /.claude/commands/create-character.md }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T12:45:56Z }
verified: { by: claude-fable-5, at: 2026-08-13T15:15:27Z }
---

# Onboarding and the death hand-off

Two flows, one shared conviction: **the mechanics are not the point, and the player should
never be made to do bookkeeping to keep playing.** Entering a world is the holodeck
door — one question, then the room. Dying costs one choice. The book stays on the
chair; do not make them wait through a census to talk to someone they came for.

## Entry: three doors, one question

"Who are you in this world?" is invoked as **`bash tools/gm-player.sh onboard <mode> [args]`**,
which runs `IdentityOnboarding.onboard()` — guard, `build()`, save, and the wiring below,
in one call (`lib/identity_onboarding.py:123`; builders at `:86`, save at `:93`, CLI at `:169`):

| Mode | Command | Where the sheet comes from |
|---|---|---|
| `canon` | `onboard canon "<NPC name>"` | that NPC's `character_sheet` if present, plus their `context` as `voice` |
| `original` | `onboard original "<name>" "<one-line concept>"` | defaults; attributes left empty and inferred against the kit |
| `nameless` | `onboard nameless` | defaults, named "A nameless traveler" |

`--json` returns the standard envelope with the saved sheet's summary
(name/race/class/level/hp/ac/stats/origin/concept/voice); a `canon` name that isn't in
`npcs.json` is an error, not a silent empty character. The `canon` name is resolved
**alias-aware** (`_find_entity_name`), so "mordecai" finds "Mordecai" and the canonical key
becomes the PC's name.

`onboard` wires the new PC in the same places [`become()`](#become-is-the-only-path-that-moves-a-sheet)
does, and for the same reason — a sheet on disk that nothing else knows about is a
half-swapped PC:

- it **refuses to overwrite a sitting PC**; `--replace` is the explicit hand-off, and it
  archives the outgoing sheet to `fallen/` before writing
- it sets `current_character` on `campaign-overview.json`, which is what session start,
  status, and world stats read
- it leaves the opening in place. In the play-pack flow **the pack is the matched
  opening**: `gm-playpack.sh set` writes `player_position` + `overview.opening_hook`
  and sets `opening_matched_to_pc: true` (see [`save_pack`](/lib/play_pack.py)), so the
  handoff's `reseed_opening` call finds the flag already true — and even when called it
  no-ops, because the play-pack flow writes no `plots.json` for it to open on. This is
  the guard that stops a later death-swap from teleporting the incoming PC onto a
  mid-campaign plot's location. `reseed_opening` still exists for the legacy plot-spine
  path (location, `overview.opening_hook`, and a `plot_local` KEY FACT
  (`Opening (not yet played): …`), chosen PC-aware from a `type:main` plot); it fires
  only while `opening_matched_to_pc` is absent/false. `--replace` after the flag is true
  is a death hand-off into a world already in play and must leave the opening; same gate
  as `set`. `/create-character` persists via `save-json`; the first `set` covers that
  path while the flag is still unset
- `canon` marks the source NPC `is_player_character` (plus `is_party_member: false` /
  `became_pc: true`) so scene context stops voicing the PC as an NPC standing nearby, and
  the lifted sheet is `status: alive` with no death stamp — the allow-list lift can't carry
  `died_at` / `cause` across

All three produce the **open** shape internally, and `save_character` persists
`to_flat(char)`. The extra keys the builders add — `voice`, `origin`, `concept` — survive
the flattening as top-level fields, which is why `origin: "canon"` is still readable on a
live sheet. See [the player character sheet](../modules/player-character.md).

This is the *default* entry path, and the three prompt surfaces that reach it say so:
`/gm`'s startup checklist and character display, `/import` Step 8, and `/new-game`'s
Phase F hand-off all route the no-character moment here. Kit-aware `/create-character`
(generic spine, or the dnd5e race/class/spell branch) is still the opt-in deep dive,
offered and never imposed. The design bet: a player arrives with an "I love this book"
spike, and spending it on ability scores wastes it.

`_default_vitals()` returns a **fresh nested dict every call** — an explicit fix for
characters aliasing one another's HP, and the reason there's a regression test for it
(`tests/test_identity_onboarding.py:45`).

## Death: persist, narrate, then offer the hand-off

Order matters and is stated in `CLAUDE.md`: persist first, narrate second, menu third.
Offering the menu before the death has landed narratively is the failure mode this
ordering exists to prevent.

1. `gm-player.sh kill "<name>" --cause "<how>"` — sets `status: dead`, HP 0, stamps
   `died_at`. Log it as a fact; record any consequence it triggers.
2. Narrate the death with weight. **No menu yet.**
3. Offer three continuations: take over a **party member**, roll a **new character**, or
   step in as a **canon figure**. (Solo with no party and no fitting canon figure: options
   2 and 3 only.) Rolling a new character spawns kit-aware `create-character` — it
   branches on the KIT block / `WorldKit.kit()`, so a Conan death does not open a 5e
   wizard builder. `CLAUDE.md` SWAP is the runtime instruction.
4. Swap, bridge the fiction, resume.

That hand-off stays the narrative default — death is meant to move the story to someone
else, not to be undone. The deliberate exit from the dead state is
`gm-player.sh revive "<name>"` (`--hp`, `--reason`), for the stories that earn it: a
resurrection, a miracle, a death the fiction walks back. It works only on the sitting PC,
never on a hero already archived to `fallen/`. See
[the player character sheet](../modules/player-character.md).

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
