---
slug: world-index-newgame-authored
title: GM authors index for bookless /new-game worlds
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: world-index
blockedBy: [world-index-schema-context]
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:19:00Z
changedFiles: [.claude/commands/new-game.md]
resolution: new-game.md item 2c directs the GM to invent + persist a same-schema World Index (write-index) for bookless worlds; rides the existing WORLD INDEX context block
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:19:00Z
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

- [x] `new-game.md` instructs the GM to author a same-schema `index` at creation
      for bookless worlds. *(item 2c: invent + persist via `gm-extract.sh write-index`)*
- [~] A creation play-through produces a populated `index` in the bible that
      matches the world's stated tone/themes. *(prompt-driven — true end-to-end proof
      is a `/new-game` play-through; the persistence path is the tested `write_index`)*
- [x] The authored index rides into scene context via the same INDEX block as the
      import path (no separate code path). *(same `write-index` → bible.index →
      WORLD INDEX block from world-index-schema-context; no new code)*

## Out of scope

- The book-backed extraction path (separate ticket).

## Verification

Lane: manual — verified by a human play-through of `/new-game` confirming a
plausible, tone-appropriate roster is authored and persisted.

## Blocked by

world-index-schema-context

---

## QA Reports

### 2026-08-15T16:19:00Z — verified, fast-lane [ss-rt14b]
- new-game.md item 2c instructs authoring a same-schema index (invented from tone/themes) and persisting via `gm-extract.sh write-index` — identical downstream to the import path (write-index → bible.index → WORLD INDEX context block, both from earlier tickets). No new code path.
- Originally kind:hitl/manual; auto-implemented per the user's "everything, prompts included" directive. Prompt-only; fast-lane. The tone-match + roster quality is a `/new-game` play-through check (marked ~).

## History

- 2026-08-15T16:19:00Z  verified (prompt-only, fast-lane; hitl auto-run per user directive) → done + committed  [ss-rt14b]
- 2026-08-15T16:19:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:19:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
