---
type: Module
title: Game core and World Kit
description: The system-agnostic engine and the per-campaign ruleset that configures it — and the two separate rule surfaces a world actually plays by.
sources:
  - { resource: /lib/game_core.py }
  - { resource: /lib/world_kit.py }
  - { resource: /lib/overview_seed.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# Game core and World Kit

`game_core.py` is the engine every world runs on; `ruleset.json` is the per-campaign
declaration of how *this* world plays; `WorldKit` binds them. The docstrings on both
modules state their own contracts. What follows is only what spans files.

## A world plays by TWO rule surfaces, not one

This is the fact that most often surprises someone editing rules, because the two live
in different files, are loaded by different code, and are surfaced to the GM differently.

| Surface | Lives in | Read by | Holds |
|---|---|---|---|
| **Mechanics** | `ruleset.json` | `WorldKit.__init__` | stat schema, progression model, resolution model, active agents |
| **World flavor** | `campaign-overview.json` → `campaign_rules` | `WorldKit.campaign_rules()` (`lib/world_kit.py:84`) | loot boxes, viewer counts, audience interviews — the signature systems |
| **Rules prose** | the file named by `ruleset.rules_doc` | `WorldKit.rules_doc_path()` | long-form rules text, loaded on demand |

Only the **flavor** surface reaches the model verbatim: the context builder prints
`campaign_rules` pretty-printed and explicitly **never truncated**, because those systems
are what make a book feel like itself. See [scene-context](scene-context.md).

Adding a signature system to `ruleset.json` instead of `campaign_rules` is therefore a
silent no-op as far as the narration is concerned. `overview_seed.py` exists because
imports used to leave `campaign_rules` empty while the book's systems lived in prose
inside a plot description.

## Three failure modes that are silent by design

The engine prefers degrading to erroring. That is deliberate — a half-authored kit should
still be playable — but it means kit bugs surface as *bland play*, not as a stack trace.

1. **Unknown progression model → milestone.** `make_progression` (`lib/game_core.py:232`)
   falls through to `MilestoneProgression` for any unrecognized name. A typo in
   `ruleset.json` (`"xp-level"` for `"xp-levels"`) costs the campaign its XP math with no
   warning anywhere.
2. **Missing ruleset → generic kit.** `WorldKit.__init__` falls back to `DEFAULT_RULESET`
   — an unnamed world with no attributes and milestone progression.
3. **Dangling `rules_doc` → `None`.** `rules_doc_path()` returns `None` when the declared
   file is absent, so a kit copied from a sibling campaign quietly loses its rules prose.
   `overview_seed.py` nulls the dangling pointer at import time rather than repairing it.

To check a live campaign rather than trusting any of this: `bash tools/gm-campaign.sh path`
then read its `ruleset.json`, or run `uv run python lib/world_kit.py info --json`.

## `spectacle_award` is a calculator, not a transaction

`spectacle_award` (`lib/game_core.py:193`) computes amounts and returns them. It reads no
files and writes none. Persistence, level-up detection, and the DCC follower co-award are
the caller's job — `gm-player.sh award` → `player_manager`. Calling the core function
directly awards nothing.

Its XP is scaled to the gap to the next level rather than being a flat table, so one tier
stays meaningful at level 1 and level 12. The `followers` amount is only applied when the
kit declares a secondary follower currency, which is why the same tier pays differently in
a Dungeon Crawler Carl campaign than in a swords-and-sorcery one.

## The kit decides which mechanics Skills are legitimate

`gm-combat`, `gm-levelup`, and `gm-spellcasting` encode D&D 5e — hit dice, spell slots, a
level-20 XP table. None of that exists in `game_core`. Loading them for a non-5e kit
imports rules the world never declared. The routing rule and its (absent) enforcement are
in [lean core and skill routing](../conventions/lean-core-and-skill-routing.md).

## Related

- [Player character](player-character.md) — where progression state is persisted
- [World bible](world-bible.md) — the prose spine a kit is drafted from
- [Authoring a world](../flows/author-a-world.md) — who writes `ruleset.json` for an original world
