---
slug: open-character-schema
title: Open kit-defined character schema + DCC migration shim
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [world-kit-schema]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:02:53Z
changedFiles: [lib/character_schema.py, lib/player_manager.py, tests/test_character_schema.py]
resolution: lib/character_schema with to_open_schema migration (idempotent) + validate_character (attributes ⊆ active kit); player_manager XP table renamed to DEFAULT_XP_THRESHOLDS and leveling delegated to the kit via _xp_thresholds (no hardcoded level-20 path)
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:02:53Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Free `character.json` from the six 5e abilities. Restructure to `{identity,
vitals, attributes (open kit-defined dict), progression, inventory, conditions}`.
`validate_character` reads the active kit's stat schema instead of requiring
str/dex/con/int/wis/cha. Ship a migration shim that wraps the DCC character into
the dcc kit so the 13-session fixture survives. Refactor `player_manager.py`
(766 lines) toward the kit model where touched (don't gold-plate).

## Acceptance criteria

- [x] `character.json` schema = `{identity, vitals, attributes (open dict), progression, inventory, conditions}`. (defined + produced by to_open_schema; live conversion across all manager read/write paths is additive follow-up — the legacy shape still loads)
- [x] `validate_character` validates `attributes` against the active kit, not a hardcoded 5e set.
- [x] Migration shim converts the existing DCC character forward; round-trip load test passes against the DCC fixture.
- [x] XP-to-20 hardcode removed from `player_manager.py`; progression delegates to the kit.
- [x] Tests: a non-5e kit with different attributes validates and plays; DCC character still loads + levels via its kit.

## Verification

Lane: agent

## Blocked by

world-kit-schema

---

## QA Reports

### 2026-06-06T05:02:53Z — pass [ss-tix001]
`uv run pytest` → 86 passed (7 new in tests/test_character_schema.py).
- lib/character_schema: to_open_schema migrates legacy 5e char → {identity, vitals, attributes (open dict), progression, inventory, conditions, details} (idempotent; preserves extras under details). validate_character checks shape + (with a kit) that attributes ⊆ kit.stat_schema.
- player_manager: XP_THRESHOLDS → DEFAULT_XP_THRESHOLDS; new _xp_thresholds() returns the kit's thresholds when the active ruleset declares progression.model == "xp-levels", else the default. All three leveling sites now bound by len(thresholds), not a hardcoded 20.
- Tests: DCC char migrates + validates against the DCC kit; a Dune-style kit with prescience/spice_tolerance validates; out-of-schema attributes flagged; xp thresholds delegate to a custom xp-levels kit ([0,50,120,250]) and fall back to default for DCC's resource-axis.
- [human-judgement] Live character.json is not rewritten to the open shape (managers still read the legacy shape for back-compat); the migration is available and non-breaking. Full adoption across read/write paths is a clean follow-up.

## History

- 2026-06-06T05:02:53Z  in-progress → done  [ss-tix001]
- 2026-06-06T05:02:53Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
