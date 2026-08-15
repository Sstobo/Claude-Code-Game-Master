---
type: Module
title: Game core and World Kit
description: The system-agnostic engine and the per-campaign ruleset that configures it — and the two separate rule surfaces a world actually plays by.
sources:
  - { resource: /lib/game_core.py }
  - { resource: /lib/world_kit.py }
  - { resource: /lib/overview_seed.py }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T16:22:00Z }
---

# Game core and World Kit

`game_core.py` is the engine every world runs on; `ruleset.json` is the per-campaign
declaration of how *this* world plays; `WorldKit` binds them. The docstrings on both
modules state their own contracts. What follows is only what spans files.

## A world plays by TWO rule surfaces, not one

This is the fact that most often surprises someone editing rules, because the two live
in different files, are loaded by different code, and used to be surfaced to the GM
from the *wrong* one.

| Surface | Lives in | Read by | Holds |
|---|---|---|---|
| **Mechanics** | `ruleset.json` | `WorldKit` | kit identity, stat schema, progression, resolution, vitals, skills, **signature_systems** |
| **Legacy flavor** | `campaign-overview.json` → `campaign_rules` | `WorldKit.campaign_rules()` | loot boxes, viewer counts — used only when the kit has no signature_systems |
| **Rules prose** | the file named by `ruleset.rules_doc` | `WorldKit.rules_doc_path()` | long-form rules text, loaded on demand |

**Signature systems on the kit ARE rendered in scene context.** YOUR WORLD'S RULES
prints `WorldKit.signature_systems()` when the ruleset has any (list form, or the
Conan dict-of-name→summary migration case — both normalize to `{name, summary}`),
never truncated. `campaign_rules` is the **legacy fallback** for campaigns that
never got systems onto the kit (DCC's fixture is this case). Adding a system to
`ruleset.json` is no longer a silent no-op.

`overview_seed.py` still exists because imports used to leave `campaign_rules` empty
while the book's systems lived in prose inside a plot description — that path still
feeds the fallback. See [scene-context](scene-context.md).

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

## Signature-system primitives are calculators, too

`game_core` ships four more world-agnostic building blocks a world's signature
systems are assembled from — every name, threshold, and die comes in as an
argument, none of it is book-specific:

- **`named_track(current, delta, config)`** — a meter with threshold
  consequences (corruption, doom, heat); applies a clamped delta and reports
  which thresholds it newly crossed, up or down. The only one that never rolls.
- **`price_roll(severity, config, rng=None)`** — what a marked action costs the
  actor; rolls, subtracts severity, and reads the cost off a ladder.
- **`reaction_roll(track_value, config, rng=None)`** — an NPC's opening
  disposition, shifted by a track/reputation value onto a tier.
- **`guarded_payoff(config, rng=None)`** — rolled before a marked treasure is
  taken; returns `clean` / `guardian_wakes` / `curse_attaches`.

Like `spectacle_award`, all four **compute and return a plain dict — they read no
files and write none**; persistence is the caller's job. Rolls are seedable via
`rng` for deterministic tests, and reuse the module dice roller when it is
omitted. `uv run python lib/game_core.py` runs their edge-case self-check.

`classify_harm(current_hp, max_hp, amount, lethality)` is the same shape — a pure
classifier returning `{new_hp, outcome}` (`ok`/`dying`/`dead`) under the kit's
`WorldKit.lethality()` model. Default `death-saves` is 5e-faithful (0 HP → dying,
massive overkill → dead); `gritty` makes 0 HP death; `massive_damage_at` lowers the
instant-death bar. The death-save ceremony itself stays in `gm-combat` / the Death
Protocol — the core only says whether a hit is survivable, dying, or fatal.

**The World Kit binds them per world** (as of 2026-08-15). `ruleset.json` may carry
a `systems` list of `{primitive, name, config}` instantiations — a Conan **Menace**
named_track, a **Sorcery's Price** price_roll — read by `WorldKit.systems()`
(malformed entries dropped) and persisted at creation by `book_bible.write_systems`
(`gm-extract.sh write-systems`). `SessionManager.get_full_context` renders them as a
distinct **YOUR WORLD'S SIGNATURE SYSTEMS (executable — ROLL these)** block, separate
from the prose YOUR WORLD'S RULES, so the GM rolls the primitives instead of narrating
by vibes. `/import` and `/new-game` author 1–3 at world creation.

## The kit decides which mechanics Skills are legitimate

`gm-combat`, `gm-levelup`, and `gm-spellcasting` encode D&D 5e — hit dice, spell slots, a
level-20 XP table. None of that exists in `game_core`. Loading them for a non-5e kit
imports rules the world never declared. The routing rule — STEP-0 defers to the
scene-context KIT block — is in [lean core and skill routing](../conventions/lean-core-and-skill-routing.md).

## Related

- [Player character](player-character.md) — where progression state is persisted
- [World bible](world-bible.md) — the prose spine a kit is drafted from
- [Authoring a world](../flows/author-a-world.md) — who writes `ruleset.json` for an original world
