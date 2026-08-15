---
slug: kit-grit-dial
title: Kit-tunable lethality (grit dial)
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: world-kit-systems
blockedBy: [system-primitives-lib]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
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

- [ ] Kit config selects the death/harm model; `game_core.py` 0-HP handling
      branches on it.
- [ ] With the default, 0-HP behavior is identical to today (death saves).
- [ ] A grittier config (e.g. lower instant-death threshold) changes 0-HP outcome
      as specified, covered by a self-check.
- [ ] No change to non-death harm resolution.

## Out of scope

- Rebalancing any specific kit's numbers (this is the dial, not the tuning).

## Verification

Lane: agent

## Blocked by

system-primitives-lib

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
