---
slug: live-state-test-stragglers
title: Two remaining test files still install fixtures into the live world-state
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: [test-fixture-isolation]
claimedBy: fable-sott1
claimedAt: 2026-08-14T13:13:08Z
changedFiles: [tests/test_persist_path_hotfixes.py, tests/test_extraction_gate.py]
resolution: the last live-state test files are hermetic; the cd regression is bound by an env-stripped test
reviewRounds: 2
implementer: null
createdAt: 2026-08-14T02:45:00Z
updatedAt: 2026-08-14T13:41:15Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

test-fixture-isolation built the GM_WORLD_STATE_BASE seam and isolated three
test files; its bisect showed tests/test_persist_path_hotfixes.py and
tests/test_extraction_gate.py still install fixture campaigns into the live
world-state and rewrite active-campaign.txt in teardown (live pointer mtime
moves on every full suite run; an interrupted run can still de-select the
player's campaign). Apply the same pattern: conftest's isolated_world_state
fixture / explicit tmp dirs; no live reads or writes.

## Acceptance criteria

- [x] Both files run entirely under tmp_path (live active-campaign.txt content AND mtime_ns unchanged across a full run of each file — the seam's guard test pattern).
- [x] Full suite passes; a full-suite run leaves the live pointer mtime untouched.

## Out of scope

Any production code; other test files.

## Verification

Lane: agent

## Blocked by

test-fixture-isolation

---

## QA Reports

### 2026-08-14T13:41:15Z — pass [review-stragglers-2]
reviewed: perfect (followup; reviewer verified the skipif guard cannot
write — NoteManager's create-on-missing is preconditioned away — and the
live facts.json mtime survived a real run). Fixture-corruption class closed.

### 2026-08-14T13:36:15Z — verified (fix round 1) [fable-sott1]
Env-stripped foreign-cwd test added and mutation-proven (cd deletion fails
it while the pinned tests pass); return codes asserted; docstrings honest;
nit taken. skipif judgment call recorded: the unpinned test reads the live
tree only when a live campaign with facts.json exists (NoteManager would
otherwise create it — the condition prevents a write). 49 tests green.

### 2026-08-14T13:30:12Z — fail [review-stragglers]
reviewed: needs-changes
1. The env pin masks the cd-PROJECT_ROOT regression the foreign-cwd tests exist to catch — need one env-stripped case.
2. Guard test ignores return codes (vacuous pass if the wrapper dies early).
3. Docstrings claim 'unread' but only content+mtime are asserted.
Nit: hand-built tmp layout duplicates the conftest convention.

### 2026-08-14T13:27:00Z — verified [fable-sott1]
48 tests across both files pass isolated; live pointer content+mtime pinned
by hand-measured sha1/mtime_ns around a full run (implementer) and guard
tests added to both files; stale _normalize_xp comment fixed. Implementer
full suite 501 passed.

## History

- 2026-08-14T02:45:00Z  created → ready (from test-fixture-isolation bisect)  [fable-sott1]
- 2026-08-14T13:13:08Z  claimed  [fable-sott1]
- 2026-08-14T13:21:01Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T13:27:00Z  verified → in-review  [fable-sott1]
- 2026-08-14T13:30:12Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-14T13:36:15Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-14T13:41:15Z  review perfect → done, committed  [fable-sott1]
