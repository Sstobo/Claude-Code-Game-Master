---
slug: executable-world-kit
title: The kit executes — resolution dispatch, kit vitals, de-5e PlayerManager
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T21:45:08Z
changedFiles: [lib/game_core.py, lib/world_kit.py, lib/player_manager.py, docs/modules/game-core-and-world-kit.md, docs/modules/player-character.md, tests/test_resolution_models.py, tests/test_milestone_progression.py]
resolution: the kit executes — declared dice resolve checks and contests, kit owns vitals/ceiling/progression, no phantom XP
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T02:36:08Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

enhancement

## What to build

The kit is descriptive, not executable. `resolution_model()`
(lib/world_kit.py:77) has no consumer — `game_core.resolve_check`
(lib/game_core.py:32-52) hardcodes 1d20/nat-20/nat-1. `stat_schema.vitals` is
enforced nowhere — conan declares hp/vigor/corruption and only hp is
trackable. PlayerManager leaks 5e: hardcoded level-20 checks
(lib/player_manager.py:311,320,426) and `_normalize_xp` (:147-161) writing a
fabricated D&D XP object onto milestone-kit characters (including via
`award_spectacle` at :361).

1. **Resolution dispatch.** `resolve_check` dispatches on the kit's
   resolution model — support at least `d20-vs-dc` (current behavior, the
   default), `2d6-plus-mod`, and `dice-pool`; unknown models warn and fall
   back to d20 (visible, not silent). Crit/fumble semantics come from the
   model.
2. **Kit vitals.** PlayerManager tracks every vital in `stat_schema.vitals`
   generically (`gm-player.sh vital <name> <±N>` or extend `hp` handling);
   `hp` remains the wired default for kits that declare it.
3. **De-5e PlayerManager.** Remove/derive the three level-20 caps from the
   kit's progression table; gate `_normalize_xp` on `progression == "xp"` so
   milestone/resource-axis characters never grow phantom XP objects.
4. First tests for the milestone path; update
   `docs/modules/game-core-and-world-kit.md` and
   `docs/modules/player-character.md` in the same commit.

## Acceptance criteria

- [x] A kit declaring `2d6-plus-mod` resolves checks with 2d6 (test with seeded RNG); dnd5e behavior is byte-identical to today.
- [x] An unknown resolution model produces a visible warning and d20 fallback, not silence.
- [x] On the conan fixture, `vigor` and `corruption` can be read and modified through the tool layer and persist to character.json.
- [x] A milestone-kit character goes through `award_spectacle` and level-up without any `xp` object appearing on their sheet.
- [x] No hardcoded `20` level caps remain in player_manager.py; caps derive from the kit's progression table.
- [x] Both claiming module docs restamped.
- [x] (review) String-shorthand progression rulesets do not crash any XP path.
- [x] (review) The 'level' progression alias awards scaled XP without a spurious warning (or is removed coherently).
- [x] (review) opposed_check resolves through the kit's model.
- [x] (review) A ruleset with no stat_schema still tracks hp.

## Out of scope

Character creation (kit-aware-character-creation), scene-context rendering
(kit-block-in-context), spell/condition skill content.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T02:36:08Z — pass [review-kit-2]
reviewed: perfect (round 2; all five closed). Nits recorded: progression_model()
reports the declared string in summary() while play uses the effective name;
_spectacle_config still reads ruleset for tier config only (guarded);
per-roll warning is documented intent. Carry-overs noted for later docs pass:
schema-reference shorthand syntax; stale _normalize_xp comment in
test_persist_path_hotfixes.

### 2026-08-14T02:32:54Z — verified (fix round 1) [fable-sott1]
47 model/progression tests pass; live probe: bare-string ruleset yields
vitals ['hp'] and milestone progression without raising; opposed pool
contest resolves. One normalizer invariant documented. Implementer full
suite 467 passed.

### 2026-08-14T02:27:52Z — fail [review-kit]
reviewed: needs-changes
1. _xp_thresholds does prog.get on the new bare-string shorthand → AttributeError on every XP path (reproduced).
2. Effective-model switch orphaned the 'level' alias: unknown-model warning + lost scaled awards.
3. opposed_check ignores the model — contests always d20 (and dc=0 is wrong for pools).
4. vitals() default only fires when ruleset.json is absent; present-but-schemaless returns [] and refuses hp.
Nit: 'warns once' docstring vs per-call warning; verified stamp on game-core doc predates rewrite.

### 2026-08-13T22:44:25Z — verified [fable-sott1]
31 new tests (19 resolution + 12 milestone) pass; live probe: 2d6 and
dice-pool models resolve, unknown model warns to stderr and falls back to
d20; _normalize_xp deleted in favor of read-only _xp_view; level ceiling
derives from the kit table; _kit_vitals routes through WorldKit. dnd5e
byte-identical (no existing test modified). Both docs restamped with
symbol cites. Implementer targeted 93/93; concurrent-tree noise on other
tickets' files attributed and excluded.

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]

## Triage note (2026-08-13, fable-sott1, from whole-branch review)

lib/player_manager.py:_kit_vitals reads ruleset.json directly (`or {}`),
skipping WorldKit's DEFAULT_RULESET fallback (vitals: ["hp"]). On a
ruleset-less campaign, WorldKit.vitals() says ['hp'] while _kit_vitals says []
and `modify_vital(..., 'hp', ...)` refuses — contradicting player-character.md.
Route _kit_vitals through WorldKit.vitals() when de-5e-ing this manager.
- 2026-08-13T21:45:08Z  claimed  [fable-sott1]
- 2026-08-13T22:44:25Z  verified → in-review  [fable-sott1]
- 2026-08-14T02:27:52Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-14T02:32:54Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-14T02:36:08Z  review perfect → done, committed  [fable-sott1]
