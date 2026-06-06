---
slug: test-harness-scaffold
title: pytest scaffold + DCC golden fixture + seam characterization snapshots
category: enhancement
kind: afk
priority: p0
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

The move-zero safety net. A pytest setup runnable via `uv`, the Dungeon Crawler
Carl (DCC) campaign frozen as a read-only golden fixture, and characterization
(snapshot) tests that capture CURRENT behavior of the two highest-risk seams —
`session_manager.get_full_context` and `consequence_manager.check_pending` —
before any later ticket changes them. This is the precondition for the whole
reimagining; every schema/behavior ticket below asserts against it.

## Acceptance criteria

- [ ] `uv run pytest` runs and is green; pytest config added to `pyproject.toml` (existing `[tool.*]` blocks present).
- [ ] A copy of the DCC campaign is checked in under `tests/fixtures/` (or referenced read-only) so tests never mutate the live campaign.
- [ ] Characterization test snapshots the current `get_full_context` output for the DCC fixture and asserts on stable substrings (location, character, pending-consequence text).
- [ ] Characterization test snapshots `check_pending` current return shape/content for the DCC fixture.
- [ ] Tests are hermetic: no network, no writes to `world-state/`, deterministic (seed any RNG).
- [ ] README/CONTRIBUTING note: how to run the suite.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
