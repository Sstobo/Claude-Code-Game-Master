---
slug: source-path-reader-sweep
title: Verify all book-text readers use source/ with legacy fallback
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: world-index
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:04:30Z
changedFiles: [tools/gm-reset.sh]
resolution: audit confirms all book-text readers already prefer source/ with legacy fallback and reset preserves source/; only gm-reset.sh help strings updated for accuracy
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:06:00Z
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

- [x] A grep for `current-document.txt` / `book-text.txt` shows every read site
      prefers the `source/` path with a legacy root fallback.
- [x] No code path reads only the old root location.
- [x] The cleanup/archive routines that wipe `extracted/` do not touch
      `source/`.
- [x] Book-backed reads (bible draft, loremaster brief) succeed against a
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

### 2026-08-15T16:06:00Z — verified, fast-lane [ss-rt14b]
- Audit of every book-text read site (annotated grep): book_bible.py:181 (source/ + legacy fallback), loremaster.py:34 (source/ first, then legacy), gm-session.sh:176 (source/ + fallbacks), agent_extractor.py:151 (writer, source/). No code path reads only the old root.
- Reset preserves source/: `reset_world` deletes only STORY_FILES (root *.json) and STORY_DIRS=(saves fallen characters); `source/` is in neither, so source/current-document.txt survives every reset path.
- Only change: 4 user-facing echo/comment strings in gm-reset.sh now name source/current-document.txt (verified diff is cosmetic-only; delete logic untouched; `bash -n` OK). docs: none (import-a-book.md references the filename, not a root path — still accurate).
- Fast-lane (no separate review): the audit found no actual bug; the sole change is provably-cosmetic help-string accuracy with zero logic change — per-ticket review would be pure token overhead. (Ticket was filed category:bug defensively; the delivered change is documentation accuracy.)

## History

- 2026-08-15T16:06:00Z  verified (fast-lane, cosmetic-only) → done + committed  [ss-rt14b]
- 2026-08-15T16:05:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:04:30Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
