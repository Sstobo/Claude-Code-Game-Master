---
type: Module
title: The player character sheet
description: Why the sheet has two shapes, which one is canonical, and how XP, death, and the spectacle award are persisted.
sources:
  - { resource: /lib/character_schema.py }
  - { resource: /lib/player_manager.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
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

## There are two `validate_character` functions

`character_schema.validate_character` requires the **open** keys (`identity`, `vitals`,
`attributes`, …) and reports a loaded flat sheet as entirely missing.
`schemas.validate_character` normalizes with `to_flat` first and accepts either. Details
and the still-red test this causes:
[two validate_character functions](../gotchas/identity-onboarding-schema-drift.md).

The open-shape one earns its place with the kit check: given a `WorldKit`, attributes
outside the kit's declared `stat_schema.attributes` are reported. An empty declared schema
disables the check entirely — which is exactly what the auto-drafted ruleset ships with,
so a freshly imported world validates everything.

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
