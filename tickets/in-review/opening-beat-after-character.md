---
slug: opening-beat-after-character
title: Seed the opening beat once the PC exists, not before
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
reviewRounds: null
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T16:20:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`gm-extract.sh seed-opening` runs during import (import.md Step 6), before the
player has a character. It picks the arc's first spine plot and writes the
starting position, the opening beat, and a session-log "Previously On" hook.

On the Conan import it seeded **The Scarlet Citadel** - a King-Conan beat that
opens with the PC already ruling Aquilonia and losing five thousand knights.
The player then chose to play the young pirate era, and every seeded artifact
was wrong: wrong location, wrong power level, wrong story. All three had to be
rewritten by hand.

The ordering is simply backwards - the opening cannot be chosen before the
protagonist is.

1. Either move `seed-opening` after character creation in the flow, or make it
   re-seed when the active PC is first set (`gm-player.sh set`).
2. When the campaign has multiple viable entry arcs, the seeded opening should
   be selectable rather than forced to spine position 1.
3. Re-seeding must rewrite the starting location, the active plot, and the
   session-log hook together - a partial re-seed is what produced the
   inconsistent state here.

## Acceptance criteria

- [ ] A fresh import followed by character creation produces an opening beat consistent with the created PC.
- [ ] Re-seeding updates player position, active plot status, and the session-log hook atomically.
- [ ] Only one plot is `active` after re-seeding (the previously seeded one is returned to available).
- [ ] A test covers import → create character → opening beat matches.

## Out of scope

The spine ordering algorithm itself.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
