---
slug: source-path-reader-sweep
title: Verify all book-text readers use source/ with legacy fallback
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: world-index
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

World Index (prds/world-index.md)

## Category

bug

## What to build

The book text moved from the campaign root to `campaigns/<name>/source/current-document.txt`
(writer + several readers already updated in-flight). Close the loop: make sure
NO reader still points only at the old root path, or a book-backed feature will
silently read nothing.

- Grep the codebase for every reader of `current-document.txt` / `book-text.txt`.
- Ensure each prefers `source/current-document.txt` and falls back to the legacy
  root path for unmigrated campaigns.
- Confirmed-updated already: `agent_extractor.py`, `book_bible.py`,
  `loremaster.py`, `gm-session.sh`. Verify these and catch any missed reader
  (e.g. gm-context / gm-lore / gm-extract paths).

## Acceptance criteria

- [ ] A grep for `current-document.txt` / `book-text.txt` shows every read site
      prefers the `source/` path with a legacy root fallback.
- [ ] No code path reads only the old root location.
- [ ] The cleanup/archive routines that wipe `extracted/` do not touch
      `source/`.
- [ ] Book-backed reads (bible draft, loremaster brief) succeed against a
      campaign whose text lives under `source/`.

## Out of scope

- The physical move of the conan file (user handles manually).
- Any change to extraction/chunking behavior.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
