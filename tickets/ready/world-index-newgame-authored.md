---
slug: world-index-newgame-authored
title: GM authors index for bookless /new-game worlds
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: world-index
blockedBy: [world-index-schema-context]
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

World Index (prds/world-index.md)

## Category

enhancement

## What to build

For original (bookless) worlds there is no RAG source to extract from, so the GM
authors the index at world-creation time from the world's established
tone/themes. Same schema, same slot in `world-bible.json`.

- `new-game.md` directs the GM to author a plausible starting roster (npcs /
  locations / items / monsters, one sentence each) that fits the world's tone and
  themes established during creation.
- Persisted through the same helper/slot as the import path so downstream
  behavior (scan → pick → materialize → save) is identical.

## Acceptance criteria

- [ ] `new-game.md` instructs the GM to author a same-schema `index` at creation
      for bookless worlds.
- [ ] A creation play-through produces a populated `index` in the bible that
      matches the world's stated tone/themes.
- [ ] The authored index rides into scene context via the same INDEX block as the
      import path (no separate code path).

## Out of scope

- The book-backed extraction path (separate ticket).

## Verification

Lane: manual — verified by a human play-through of `/new-game` confirming a
plausible, tone-appropriate roster is authored and persisted.

## Blocked by

world-index-schema-context

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
