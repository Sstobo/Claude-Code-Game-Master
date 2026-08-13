---
slug: extraction-output-verification
title: Verify agent output exists, is non-empty, and matches runtime shape before the next stage
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T18:54:15Z
changedFiles: [tools/gm-extract.sh, lib/minor_stubs.py, '.claude/commands/import.md', docs/import-guide.md, tests/test_extraction_gate.py]
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T19:23:30Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Every extraction stage trusts the previous stage's REPORT rather than its
OUTPUT. Three failures observed in one Conan import:

1. **An agent claimed success having written nothing.** The NPC extractor
   returned a completion summary describing work it had not done;
   `extracted/` was empty. Caught only by a manual `ls`.
2. **`validate` miscounts list-shaped JSON.** The items extractor correctly
   followed `ITEM_SCHEMA` (a flat list) and wrote 43 items;
   `gm-extract.sh validate` reported `items: EMPTY (0 entities)`. It counts
   dict keys and silently reads 0 for a list.
3. **`validate` passes on empty-but-present files.** It printed
   "All files valid" while npcs.json and locations.json were `{}`.

Fixes:

- `validate` must handle both list and dict shapes and report true counts.
- `validate` must FAIL (non-zero) when a required file is missing or has zero
  entities, not print a warning inside a success message.
- Add a shape-normalizing step (or extend `normalize`) that accepts either a
  list or a dict from any extractor and always writes the flat
  `{name: {...}}` runtime shape - the list/dict mismatch between
  `extraction_schemas.py` and the runtime managers is the root cause of (2).
- The import flow must run this gate after the agents and refuse to proceed to
  `cap`/`reconcile`/`integrity` on failure.

## Acceptance criteria

- [x] `validate` reports 43 for a 43-element list-shaped items.json (regression test with a list fixture).
- [x] `validate` exits non-zero when any required extraction file is missing or empty.
- [x] `normalize` accepts list-shaped and dict-shaped input for all four types and always emits the flat keyed runtime shape.
- [x] The import flow halts with a clear message when the gate fails, naming which type failed and why.
- [x] Existing tests still pass (`uv run --extra dev pytest`).
- [x] (review) Non-scalar entity names produce a named validate failure, never a traceback.
- [x] (review) Step 5.5 "continue with partial data" has a mechanical bypass or is removed.
- [x] (review) import-guide.md sources: includes /lib/minor_stubs.py.
- [x] (review) Wrapper unwrap cannot reduce a legit keyed dict to empty on a wrapper-key collision.

## Out of scope

Making the extractor agents themselves more reliable (see subagent-fanout-cap).
Do not change ITEM_SCHEMA's documented shape - normalize around it.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T19:23:30Z — pass [review-extract-2]
reviewed: perfect (followup; two non-blocking keyed-dict edge notes recorded).
Pre-commit truth fix by orchestrator (doc/comment text only, no behavior):
four sites claimed extraction_schemas declares lists — it declares keyed
dicts; wording corrected to name real agent drift as the list source
(minor_stubs docstrings, test docstring, import-guide sentence). Gate tests
re-run green after the wording fix.

### 2026-08-13T19:19:28Z — verified (fix round 1) [fable-sott1]
38/38 gate tests; ValueError-named failures verified live (no traceback);
wrapper-collision case survives; all-or-nothing normalize; partial-data
option removed with reasoning documented. Implementer full suite 372 passed.

### 2026-08-13T19:15:24Z — fail [review-extract]
reviewed: needs-changes
1. import.md:277/289 — 'Continue with partial data' option mechanically unreachable now that Step 6 re-asserts validate under set -e.
2. minor_stubs.py:49 — non-scalar name raises TypeError traceback (contract says named failure); mid-chain abort leaves partial writes.
3. import-guide.md describes normalize_entity_shape but does not claim /lib/minor_stubs.py in sources.
Non-blocking: wrapper-key collision silently yields an empty result (worst direction for warn-and-pass types); duplicate names collapse silently; EXTRACTION_TYPES only half-applied (gm-extract.sh:462); import-a-book.md normalize line slightly stale.

### 2026-08-13T19:11:21Z — verified [fable-sott1]
24/24 gate tests; validate counts both shapes, hard-fails empty npcs/locations,
warns-and-passes empty items/plots (reasoned + documented); normalize shares
one shape rule (normalize_entity_shape); import.md gate is mechanical (set -e
+ re-assert). import-guide.md restamped. Implementer full suite 358 passed.

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-13T18:54:15Z  claimed  [fable-sott1]
- 2026-08-13T19:06:36Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T19:11:21Z  verified → in-review  [fable-sott1]
- 2026-08-13T19:15:01Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T19:15:24Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T19:19:28Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T19:23:30Z  review perfect → done, committed  [fable-sott1]
