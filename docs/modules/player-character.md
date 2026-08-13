---
type: Module
title: The player character sheet
description: Why the sheet has two shapes, which one is canonical, and how XP, death, and the spectacle award are persisted.
sources:
  - { resource: /lib/character_schema.py }
  - { resource: /lib/player_manager.py }
  - { resource: /features/character-creation/save_character.py }
generated: { by: claude-opus-5, at: 2026-08-13T18:47:33Z }
---

# The player character sheet

## Flat is canonical; open is a legacy input

Two shapes exist, and only one is written: **flat** (`name`, `hp`, `stats`, `level`,
`gold` as top-level keys) is what the entire runtime reads — `player_manager`, the session
brief, `gm-campaign.sh list`, and the jq statusline. The **open** shape
(`identity`/`vitals`/`attributes`/…) is accepted on read and converted.

`to_flat` and `to_open_schema` are lossless inverses. That matters for kit-agnosticism: a
kit vital the schema has never heard of (`water`, `heat`, `corruption`) survives a
round-trip because unrecognized keys are swept into `details` on the way out and lifted
back to the top level on the way in. `stats` is an open dict, so "flat" does not mean
"D&D's six abilities" despite the legacy field names.

**Migration happens on first read.** `_normalize_loaded` (`lib/player_manager.py:113`)
converts an open-schema file and **writes it back immediately**. So loading a legacy
character mutates it on disk as a side effect — expected, but surprising the first time a
read-only operation dirties the campaign.

## Kit vitals are tracked, not just carried

Surviving the round-trip is the floor, not the ceiling. Any vital the active kit declares
in `ruleset.json` → `stat_schema.vitals` is readable and writable through
`modify_vital` (`lib/player_manager.py`) and `gm-player.sh vital <vital> <±N|set N>` — the
argument is the vital's name, not a character's, unlike every sibling verb — and appears in
`show` output. The declaration is the authority: a vital the kit never declared is refused
rather than silently created, so a typo does not quietly grow a new track.

Two shapes are honored because sheets use both — a `{current, max}` dict clamps to its max
and stays a dict, a plain number stays a plain number. `hp` is declared like any other
vital but keeps its dedicated path: a `vital hp` call delegates to `modify_hp`, so the
dying gate described under [death](#death-is-a-state-not-a-deletion) still fires. That
delegated result is re-keyed to `vital`/`previous`/`current`/`max` (keeping `modify_hp`'s
own keys) so one verb never returns two response shapes.

`save_character.py` is kit-aware at the same boundary. It takes the kit's own stat key
`attributes` (`stats` remains a legacy alias) and derives HP from the class hit die + CON
and writes a 5e `saves` block **only** when the active kit is `dnd5e`. An authored HP is
preserved verbatim in **every** kit, `dnd5e` included — authoring beats deriving, so a
rolled or hand-tuned sheet is never silently recomputed. Declared kit vitals supplied at
creation are carried onto the sheet. See [the schema reference](../schema-reference.md) for
where the declaration lives.

## One validator: `schemas.validate_character`

Shape-agnostic (normalizes via `to_flat`), kit-aware: given a `WorldKit`, stats outside
the kit's declared `stat_schema.attributes` are reported. Only `name` and `level` are
required — `race`/`class` are 5e-flavored and legitimately absent on a nameless traveler
or a non-D&D character. Two caveats: an empty declared stat schema disables the kit check
(which is what the auto-drafted ruleset ships with), and the open-vs-flat trap that once
produced a duplicate validator still exists at the builder boundary — see
[the shape trap](../gotchas/identity-onboarding-schema-drift.md).

## XP delegates to the kit, then falls back

`_xp_thresholds` (`lib/player_manager.py:135`) reads `ruleset.json` and uses the kit's
thresholds **only when the model is `xp-levels` and thresholds are present**. Anything
else — milestone kits, resource-axis kits, an `xp-levels` kit that forgot its table —
silently uses `DEFAULT_XP_THRESHOLDS`. So a milestone world still accrues levels if
something calls `award_xp`.

`award_xp` prints the literal token `LEVEL_UP` on a level gain, and `get_xp_status` prints
`READY_TO_LEVEL_UP`. Those strings are the interface: the GM watches for them to trigger
the level-up ceremony. Changing their wording breaks the routing described in
[lean core and skill routing](../conventions/lean-core-and-skill-routing.md).

## Spectacle awards route back through `award_xp`

`award_spectacle` computes amounts via `game_core.spectacle_award`, then — for XP-based
kits — applies them **through `award_xp`** rather than writing XP directly
(`lib/player_manager.py:378`), specifically so `LEVEL_UP` detection still fires. A
spectacle beat can therefore level the character, which is the point: non-kill
achievements advance the same axis kills do. See
[game core and World Kit](game-core-and-world-kit.md).

## Death is a state, not a deletion

`kill_character` sets `status: 'dead'`, HP to 0, and stamps `died_at` + cause. The sheet
stays. `become(npc_name)` then copies a party member's sheet into `character.json` and
archives the fallen PC to `fallen/<name>-<id>.json`, clearing `died_at` and the dead status
on the new sheet. Nothing is destroyed, which is what lets the world keep referencing,
mourning, and avenging the dead hero.

`modify_hp` guards on `status != 'dead'` (`lib/player_manager.py:468`) — a corpse does not
take damage.

## Related

- [Onboarding and death hand-off](../flows/onboarding-and-death.md) — the flows that call these
- [NPC model](npc-model.md) — party members carry a parallel `character_sheet`
