---
slug: open-character-schema
title: Open kit-defined character schema + DCC migration shim
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [world-kit-schema]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
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

- [ ] `character.json` schema = `{identity, vitals, attributes (open dict), progression, inventory, conditions}`.
- [ ] `validate_character` validates `attributes` against the active kit, not a hardcoded 5e set.
- [ ] Migration shim converts the existing DCC character forward; round-trip load test passes against the DCC fixture.
- [ ] XP-to-20 hardcode removed from `player_manager.py`; progression delegates to the kit.
- [ ] Tests: a non-5e kit with different attributes validates and plays; DCC character still loads + levels via its kit.

## Verification

Lane: agent

## Blocked by

world-kit-schema

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
