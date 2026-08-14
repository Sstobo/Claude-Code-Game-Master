---
slug: test-fixture-isolation
title: Wave-1 test fixtures mutate live world-state (active-campaign.txt, campaigns/, archive perms)
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T02:36:36Z
changedFiles: [tools/common.sh, lib/campaign_manager.py, tests/conftest.py, tests/test_reset_archive.py, tests/test_active_campaign_guard.py, tests/test_bootstrap_no_campaign.py, docs/conventions/tool-wrapper-contract.md]
resolution: GM_WORLD_STATE_BASE seam; campaign tests run under tmp_path and cannot touch live state
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T18:45:00Z
updatedAt: 2026-08-14T12:25:26Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

From review-bootstrap: tests/test_active_campaign_guard.py,
tests/test_bootstrap_no_campaign.py, and tests/test_reset_archive.py all
mutate the real repo — they unlink the live world-state/active-campaign.txt,
create fixture campaigns under world-state/campaigns/, and chmod the real
world-state/archive. A hard-killed run leaves the player with no active
campaign; `pytest -n auto` races the two no-campaign fixtures; a stale
pytest-reset-fixture dir breaks later runs.

Route the tools through an isolated world-state root instead: the cleanest
seam is an env var (e.g. `GM_WORLD_STATE_BASE`) honored by tools/common.sh and
lib json_ops path resolution, with tests pointing it at tmp_path. If that seam
is too invasive, at minimum: session-scoped lockfile so the fixtures can't
race, stale-fixture cleanup at session start, and addopts guarding against -n.

## Acceptance criteria

- [x] Tests touching campaign state run entirely under tmp_path (or the fallback guards above are all in place).
- [x] `pytest -n 4` on the three files passes repeatedly.
- [x] A killed run cannot leave active-campaign.txt missing (verify by construction).
- [x] Full suite passes.

## Out of scope

Rewriting unrelated existing tests; CI configuration.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T12:25:26Z — pass [review-fixtures]
reviewed: perfect. Reviewer verified a 1173-entry live-tree snapshot is
bit-identical across runs. Notes: (1) GM_WORLD_STATE_BASE in .env would
split-brain bash vs python (env sourced after the assignment) — recorded,
not reachable today; (2) tool-wrapper-contract lacked the campaign_manager
source claim — added pre-commit (frontmatter only).

### 2026-08-14T12:18:01Z — verified [fable-sott1]
Seam works (env probe returns the tmp base); 55 tests across the three
files pass; SIGKILL interrupt leaves live state byte- and mtime-identical;
3x parallel rounds green. Straggler files (persist-hotfixes, extraction-
gate) bisected and filed as live-state-test-stragglers (declared out of
this ticket's confirmed scope). Implementer full suite 487 passed.

## History

- 2026-08-13T18:45:00Z  created → ready (from review-bootstrap findings)  [fable-sott1]

## Triage note (2026-08-13, fable-sott1, from review-bootstrap's late verdict)

Concrete criteria to absorb:
- Save/restore of active-campaign.txt must be an atomic rename
  (os.replace to a sidecar and back), never delete-and-rewrite-from-memory —
  a SIGKILL mid-run must leave the file on disk with original content.
- A test asserts post-fixture restoration: active-campaign.txt exists with
  byte-identical content after the fixture completes.
- Each no-campaign wrapper invocation asserts a command-specific expected
  string (e.g. gm-extract.sh's usage header), not merely non-empty output.
- 2026-08-14T02:36:36Z  claimed  [fable-sott1]
- 2026-08-14T12:08:44Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T12:18:01Z  verified → in-review  [fable-sott1]
- 2026-08-14T12:25:26Z  review perfect → done, committed  [fable-sott1]
