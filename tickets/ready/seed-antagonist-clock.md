---
slug: seed-antagonist-clock
title: Every new campaign ships with an off-screen antagonist clock
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: living-world
blockedBy: []
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

Living World (prds/living-world.md)

## Category

enhancement

## What to build

A stage without a countdown is inert (Yara shipped with no clock, no plan). Give
every new campaign a spine: at least one antagonist/threat clock whose aim
completes off-screen, seeded at creation. Still one stage — but a live one.

- `/import` and `/new-game` seed ≥1 `threat-clocks.json` clock representing the
  antagonist's off-screen aim. Import grounds it in extracted plots; new-game
  authors it from tone/themes.
- Does NOT pre-build the world beyond this — one clock, not a gazetteer.

## Acceptance criteria

- [ ] After `/import`, `threat-clocks.json` contains ≥1 seeded antagonist clock
      with a name, segments, and a consequence, grounded in the source.
- [ ] After `/new-game`, the same holds, authored from the world's tone/themes.
- [ ] The seeded clock is a valid clock (advances via the existing
      `gm-clock.sh` machinery).
- [ ] Seeding adds exactly the spine (no cascade of pre-built content).

## Out of scope

- The graph edges (separate ticket) and any broader world pre-build.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
