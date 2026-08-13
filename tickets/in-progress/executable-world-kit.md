---
slug: executable-world-kit
title: The kit executes — resolution dispatch, kit vitals, de-5e PlayerManager
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
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

- [ ] A kit declaring `2d6-plus-mod` resolves checks with 2d6 (test with seeded RNG); dnd5e behavior is byte-identical to today.
- [ ] An unknown resolution model produces a visible warning and d20 fallback, not silence.
- [ ] On the conan fixture, `vigor` and `corruption` can be read and modified through the tool layer and persist to character.json.
- [ ] A milestone-kit character goes through `award_spectacle` and level-up without any `xp` object appearing on their sheet.
- [ ] No hardcoded `20` level caps remain in player_manager.py; caps derive from the kit's progression table.
- [ ] Both claiming module docs restamped.

## Out of scope

Character creation (kit-aware-character-creation), scene-context rendering
(kit-block-in-context), spell/condition skill content.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]

## Triage note (2026-08-13, fable-sott1, from whole-branch review)

lib/player_manager.py:_kit_vitals reads ruleset.json directly (`or {}`),
skipping WorldKit's DEFAULT_RULESET fallback (vitals: ["hp"]). On a
ruleset-less campaign, WorldKit.vitals() says ['hp'] while _kit_vitals says []
and `modify_vital(..., 'hp', ...)` refuses — contradicting player-character.md.
Route _kit_vitals through WorldKit.vitals() when de-5e-ing this manager.
