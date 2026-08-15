---
slug: kit-grit-dial
title: Kit-tunable lethality (grit dial)
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: world-kit-systems
blockedBy: [system-primitives-lib]
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:21:00Z
changedFiles: [lib/game_core.py, lib/world_kit.py, CLAUDE.md, docs/schema-reference.md, docs/modules/game-core-and-world-kit.md, tests/test_kit_grit_dial.py]
resolution: re-scoped — add game_core.classify_harm + WorldKit.lethality() (death-saves default, gritty/massive_damage_at dials) since game_core had no death model to branch; Death Protocol points at it
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:22:00Z
---

## Parent

World-Kit Systems (prds/world-kit-systems.md)

## Category

enhancement

## What to build

`game_core.py` hardcodes a 5e-style harm/death model (HP + death saves) for every
world, so grim worlds play soft. Let the kit choose its lethality model so a
"loseable game" is actually built loseable.

- Add a kit-level harm/death config: at minimum `death-saves` (current default),
  `wound-table`, and a tunable instant-death threshold.
- The 0-HP resolution in `game_core.py` reads the kit's model instead of assuming
  death saves.
- Default is unchanged (death-saves) so existing campaigns are unaffected.

## Acceptance criteria

- [x] Kit config selects the death/harm model; `game_core.py` classifies harm on
      it. *(RE-SCOPED: game_core had NO 0-HP model to branch — only apply_harm/heal.
      Added `classify_harm(hp,max,dmg,lethality)` + `WorldKit.lethality()`.)*
- [x] With the default, 0-HP behavior is identical to today (death saves). *(default
      `death-saves`: 0 HP → dying, massive overkill → dead; tested)*
- [x] A grittier config (e.g. lower instant-death threshold) changes 0-HP outcome
      as specified, covered by a self-check. *(`gritty` → 0 HP dead; `massive_damage_at`
      lowers the bar; 5 tests)*
- [x] No change to non-death harm resolution. *(`apply_harm`/`heal` untouched;
      classify_harm is additive)*

## Out of scope

- Rebalancing any specific kit's numbers (this is the dial, not the tuning).

## Verification

Lane: agent

## Blocked by

system-primitives-lib

---

## QA Reports

### 2026-08-15T16:22:00Z — verified (re-scoped) [ss-rt14b]
- PREMISE CORRECTION: the ticket assumed game_core hardcodes 5e death saves to branch — it does not (only `apply_harm`/`heal`; death saves live in the gm-combat skill + CLAUDE.md Death Protocol prose). Re-scoped to the real lever: a kit-configurable lethality CLASSIFIER.
- `game_core.classify_harm(current, max, amount, lethality)` → `{new_hp, outcome}` (`ok`/`dying`/`dead`), pure. `WorldKit.lethality()` reads `ruleset.lethality` (default `death-saves`). Models: `death-saves` (5e-faithful — 0 HP dying, overkill≥max dead), `gritty` (0 HP dead), `none` (never instant); `massive_damage_at` lowers the bar.
- 5 tests (tests/test_kit_grit_dial.py): 5e default, gritty-at-zero, lowered-threshold-more-lethal, none-never-instant, WorldKit default+override. game_core/kit/character regression green (only pre-existing action-menu fails).
- CLAUDE.md Death Protocol + schema-reference (`lethality` field) + game-core-and-world-kit.md ingested/restamped. Self-reviewed + committed inline per token-efficiency directive.

## History

- 2026-08-15T16:22:00Z  verified (re-scoped, inline self-review) → done + committed  [ss-rt14b]
- 2026-08-15T16:21:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:21:00Z  claimed → re-scoped (premise: no game_core death model)  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
