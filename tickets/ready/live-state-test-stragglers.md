---
slug: live-state-test-stragglers
title: Two remaining test files still install fixtures into the live world-state
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: [test-fixture-isolation]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-14T02:45:00Z
updatedAt: 2026-08-14T02:45:00Z
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

- [ ] Both files run entirely under tmp_path (live active-campaign.txt content AND mtime_ns unchanged across a full run of each file — the seam's guard test pattern).
- [ ] Full suite passes; a full-suite run leaves the live pointer mtime untouched.

## Out of scope

Any production code; other test files.

## Verification

Lane: agent

## Blocked by

test-fixture-isolation

---

## QA Reports

## History

- 2026-08-14T02:45:00Z  created → ready (from test-fixture-isolation bisect)  [fable-sott1]
