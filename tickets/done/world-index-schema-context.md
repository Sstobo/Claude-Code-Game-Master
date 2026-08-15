---
slug: world-index-schema-context
title: Index schema + rides into scene context + GM guidance
category: enhancement
kind: afk
priority: p0
lane: agent
parentPrd: world-index
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T15:40:51Z
changedFiles: [lib/book_bible.py, lib/world_bible.py, lib/session_manager.py, CLAUDE.md, docs/modules/world-bible.md, docs/modules/scene-context.md, docs/schema-reference.md, tests/test_world_index_context.py, tests/test_bible_kit_chain.py]
resolution: replace junk bible chapters with an index (npcs/locations/items/monsters) and wire a WORLD INDEX block into scene context
reviewRounds: 1
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:53:30Z
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

- [x] The bible skeleton/validator accepts `index` with the four buckets and
      rejects malformed entries; `chapters` is no longer part of the schema.
- [x] `segment_into_chapters()` is no longer invoked to build the bible (dead
      code either removed or clearly unreferenced by the bible path).
- [x] `bash tools/gm-session.sh context` emits an INDEX block sourced from the
      bible's `index` when entries exist, and omits it cleanly when empty.
- [x] CLAUDE.md carries a one-line instruction to scan the index before
      inventing an entity name.
- [x] Existing bible fields (voice, tone, themes, factions, geography) still load
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

### 2026-08-15T15:53:30Z — pass [reviewer]
reviewed: perfect — independently confirmed no remaining readers of `bible['chapters']`, the removed `max_chars` param has no callers, and `_index_errors` (requiring `note`) is consistent with the schema and the context renderer; no correctness regressions in scope. Out-of-scope findings (game_core seeded dice, gm-reset text, a pre-existing duplicated source-path resolver at book_bible.py:181) belong to other agents' concurrent changes and were not folded in.
Notes: two doc line-number nits (scene-context.md cited session_manager.py:526/:826) — FIXED in this commit to :592/:932 (and :891→:997) since the doc was restamped fresh.

### 2026-08-15T15:48:52Z — verified [ss-rt14b]
- `chapters` removed from bible schema; `index` (npcs/locations/items/monsters) scaffolded empty; `validate_bible` accepts good/absent index, rejects missing-note and non-list buckets.
- Net-new WORLD INDEX block emitted by `get_full_context` when the bible carries an index; absent/empty index emits no header. Proven by adversarial qaEval `tests/test_world_index_context.py` (5/5).
- `segment_into_chapters` intact and still referenced by the RAG coarse index (`lib/rag/coarse_index.py`); `test_coarse_index` + `test_book_bible_import` + `test_loremaster` still green.
- Updated stale characterization test `test_bible_kit_chain.py` to the new no-chapters/index contract. Full touched-surface suite: 48 passed.
- [pre-existing, out of scope] `test_get_full_context.py::test_action_menu_on_is_a_few_numbered_not_exactly_three` fails on HEAD independent of this ticket (committed code says "exactly THREE" while the stale test expects "a few numbered"). Not touched.

## History

- 2026-08-15T15:53:30Z  review perfect (2 doc nits fixed) → done + committed  [ss-rt14b]
- 2026-08-15T15:48:52Z  verified → in-review  [ss-rt14b]
- 2026-08-15T15:41:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T15:40:51Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
