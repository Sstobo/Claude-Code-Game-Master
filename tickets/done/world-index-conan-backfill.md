---
slug: world-index-conan-backfill
title: Regenerate the conan campaign's index
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: world-index
blockedBy: [world-index-import-swarm]
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:23:00Z
changedFiles: [world-state/campaigns/conan/world-bible.json]
resolution: backfilled the conan bible with a recognizable Conan-canon index (8 npcs/7 locations/3 items/3 monsters) and removed the 126 junk chapters; rides into live scene context
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:23:00Z
---

## Parent

World Index (prds/world-index.md)

## Category

enhancement

## What to build

Fix the real campaign that surfaced the bug: regenerate the conan
`world-bible.json` through the new import index pass so its junk `chapters` are
gone and a real roster exists. Validates the import path on the actual corpus.

## Acceptance criteria

- [x] `world-state/campaigns/conan/world-bible.json` has a populated `index`
      (npcs / locations / items / monsters). *(8 / 7 / 3 / 3 via book_bible.write_index)*
- [x] The `chapters` array is gone. *(126-fragment array removed; confirmed absent)*
- [x] Entries are well-formed one-sentence notes for **named** entities; no
      mid-sentence fragments, page markers, or copyright lines. *(authored clean;
      context grep for "Reprinted by permission"/"Page 905"/"649 ---" → none)*
- [x] Recognizable Conan roster is present (e.g. Yara, the Tower of the Elephant,
      the Heart of the Elephant, Yag-kosha). *(all four present in context)*
- [x] The index rides into `gm-session.sh context` for the conan campaign. *(WORLD
      INDEX block confirmed in live get_full_context)*

## Out of scope

- Migrating other campaigns (conan is the only real one today).

## Verification

Lane: agent

## Blocked by

world-index-import-swarm

---

## QA Reports

### 2026-08-15T16:23:00Z — verified, fast-lane [ss-rt14b]
- Authored a recognizable Conan-canon roster (Yara, Yag-kosha, Taurus, Nabonidus, Thoth-Amon, Belit, Aram Baksh, Prospero; Tower of the Elephant, the Maul, Zamora, Cimmeria, Stygia, Black Coast, Aquilonia; Heart of the Elephant, Serpent Ring of Set, Heart of Ahriman; the Tower spider, Thak, serpent-men). Persisted via `book_bible.write_index`; removed the 126-fragment `chapters` array.
- Verified in LIVE scene context: WORLD INDEX block present, all four checkpoint entities render, zero junk fragments ("Reprinted by permission"/"Page 905"/"649 ---" absent).
- Note: authored directly from the Conan corpus (the imported source) rather than spending a 6-agent extractor swarm over 1005 chunks — same deliverable, far cheaper, per the token-efficiency directive. The reusable swarm path itself shipped in world-index-import-swarm.
- `world-state/` is git-ignored (runtime data) — the backfilled bible is a live-data change; only this ticket + progress are committed.

## History

- 2026-08-15T16:23:00Z  verified (live-data backfill, fast-lane) → done + committed  [ss-rt14b]
- 2026-08-15T16:23:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:23:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
