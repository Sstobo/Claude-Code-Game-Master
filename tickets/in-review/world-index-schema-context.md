---
slug: world-index-schema-context
title: Index schema + rides into scene context + GM guidance
category: enhancement
kind: afk
priority: p0
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

enhancement

## What to build

Replace the junk `chapters` array in the world-bible with an `index` structure,
and make it actually reach the GM. This is the foundation the two generation
paths (import swarm, new-game authored) and the conan backfill build on.

- Add `index` to the bible skeleton/schema with four buckets: `npcs`,
  `locations`, `items`, `monsters`. Each entry `{"name": str, "note": str}`
  (one sentence).
- Remove the `chapters` field from the bible structure; stop using
  `segment_into_chapters()` to populate the bible.
- Wire the index into scene context: `session_manager.py` must emit an INDEX
  block from the bible (today only `voice` is read). Confirm it appears in
  `gm-session.sh context` output.
- Add a one-line note to CLAUDE.md's play/search flow: the GM scans the index
  before inventing a name.

## Acceptance criteria

- [ ] The bible skeleton/validator accepts `index` with the four buckets and
      rejects malformed entries; `chapters` is no longer part of the schema.
- [ ] `segment_into_chapters()` is no longer invoked to build the bible (dead
      code either removed or clearly unreferenced by the bible path).
- [ ] `bash tools/gm-session.sh context` emits an INDEX block sourced from the
      bible's `index` when entries exist, and omits it cleanly when empty.
- [ ] CLAUDE.md carries a one-line instruction to scan the index before
      inventing an entity name.
- [ ] Existing bible fields (voice, tone, themes, factions, geography) still load
      and emit unchanged.

## Out of scope

- Populating the index from the book (import swarm) or authoring it for bookless
  worlds — separate tickets.
- Any change to the RAG/vector pipeline.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
