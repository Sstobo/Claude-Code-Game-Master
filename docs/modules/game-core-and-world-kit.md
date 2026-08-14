---
type: Module
title: Game core and World Kit
description: The system-agnostic engine and the per-campaign ruleset that configures it — and the two separate rule surfaces a world actually plays by.
sources:
  - { resource: /lib/game_core.py }
  - { resource: /lib/world_kit.py }
  - { resource: /lib/overview_seed.py }
generated: { by: claude-opus-5, at: 2026-08-14T02:30:38Z }
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
| **World flavor** | `campaign-overview.json` → `campaign_rules` | `WorldKit.campaign_rules()` | loot boxes, viewer counts, audience interviews — the signature systems |
| **Rules prose** | the file named by `ruleset.rules_doc` | `WorldKit.rules_doc_path()` | long-form rules text, loaded on demand |

Only the **flavor** surface reaches the model verbatim: the context builder prints
`campaign_rules` pretty-printed and explicitly **never truncated**, because those systems
are what make a book feel like itself. See [scene-context](scene-context.md).

Adding a signature system to `ruleset.json` instead of `campaign_rules` is therefore a
silent no-op as far as the narration is concerned. `overview_seed.py` exists because
imports used to leave `campaign_rules` empty while the book's systems lived in prose
inside a plot description.

## The resolution model is executed, not just declared

`resolution.model` picks the dice a check is actually rolled on — `resolve_check`
dispatches on it, so a 2d6 world rolls 2d6 rather than a d20 wearing a 2d6 label. Three
models ship:

| Model | Roll | Success | Crit / fumble |
|---|---|---|---|
| `d20-vs-dc` (default) | 1d20 + mod | total ≥ DC | natural 20 / natural 1 |
| `2d6-plus-mod` | 2d6 + mod | total ≥ DC | 12 / 2 |
| `dice-pool` | N d6, N = the modifier (min 1) | successes ≥ DC | all dice hit / none do |

All three return the same keys (`die`, `modifier`, `total`, `dc`, `success`, `margin`,
`critical`), so callers do not branch. In the pool, `die` carries the success count and
`modifier` the pool size, and the DC is **successes required**, not a total to beat. The
face that counts as a success is `target` (default 5), and `advantage`/`disadvantage`
means an extra/fewer die rather than a second d20.

`opposed_check` takes the same optional `model` and rolls both sides on it, ranking them
on that model's own axis — totals for d20 and 2d6, success counts for a pool. A contest
has no DC, so each side is resolved at DC 0 and only its axis value is read.

The `model` argument is optional on both and defaults to `d20-vs-dc`, which is why every
pre-existing caller — including the whole `dnd5e` path — is unaffected. `WorldKit.resolve()`
and `WorldKit.oppose()` are the doors that supply the campaign's model.

## Ruleset syntax is normalized before the core sees it

A kit may write `"resolution": "dice-pool"` or `{"model": "dice-pool", "target": 4}`;
`WorldKit.resolution()` returns `{model, params}` either way, and `progression` accepts the
same string shorthand. `level` is an accepted alias for `xp-levels` in both
`make_progression` and `spectacle_award`.

Nothing outside `WorldKit` may re-parse `ruleset.json` for these fields. `player_manager`
asks the kit — vitals from `vitals()`, thresholds off the built `progression` object — so a
syntax the kit accepts can never crash a sheet operation, and there is exactly one place a
new shorthand has to be taught.

## Failure modes: two silent, one now audible

The engine prefers degrading to erroring — a half-authored kit should still be playable —
but it means kit bugs surface as *bland play*, not as a stack trace. Both fallbacks that
would silently swap out a world's math now say so.

1. **Unrecognized model name → a warning, then the default.** `make_progression` falls
   through to `MilestoneProgression` and `resolve_check` falls back to `d20-vs-dc`, but
   each prints a one-line `[WARNING]` naming the offending value. A typo in `ruleset.json`
   (`"xp-level"` for `"xp-levels"`) still costs the campaign its XP math, but it no longer
   does it invisibly. The warnings go to **stderr**, never stdout, so `--json` output on
   the tool wrappers stays parseable.
2. **Missing ruleset → generic kit.** `WorldKit.__init__` falls back to `DEFAULT_RULESET`
   — an unnamed world with no attributes, milestone progression, and `hp` as its one
   vital. `vitals()` returns `['hp']` for an under-declared kit too (no `stat_schema`, or
   an empty list), because every world has a body and a kit half-authored into silence
   should not refuse plain damage.
3. **Dangling `rules_doc` → `None`.** `rules_doc_path()` returns `None` when the declared
   file is absent, so a kit copied from a sibling campaign quietly loses its rules prose.
   `overview_seed.py` nulls the dangling pointer at import time rather than repairing it.

To check a live campaign rather than trusting any of this: `bash tools/gm-campaign.sh path`
then read its `ruleset.json`, or run `uv run python lib/world_kit.py info --json`.

## `spectacle_award` is a calculator, not a transaction

`spectacle_award` (`lib/game_core.py`) computes amounts and returns them. It reads no
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
