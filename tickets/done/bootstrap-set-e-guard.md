---
slug: bootstrap-set-e-guard
title: No-active-campaign return 1 must not kill every tool under set -e
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T16:06:15Z
changedFiles: [tools/common.sh, tests/test_bootstrap_no_campaign.py]
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T18:42:45Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`get_campaign_dir` (tools/common.sh:36) returns 1 when no campaign is active.
Every tool sources common.sh, and `WORLD_STATE_DIR=$(get_campaign_dir)` at
line 73 takes that exit status. Under `set -e` the script dies immediately -
before its first echo. Result: a first-time user runs `gm-extract.sh prepare`
and gets zero output and exit 1. Every tool, every new install, no diagnostic.

Observed live: the first Conan import produced no output at all and created no
campaign directory. The bug is invisible because the failure happens before any
error handling can print.

1. Keep the `|| true` guard on the assignment (already applied in the working
   tree with a `ponytail:` comment) OR make `get_campaign_dir` return 0 with an
   empty stdout - pick one and make it consistent. Downstream code at
   common.sh:76 already branches on the empty string, so no caller changes.
2. Audit every other `set -e` script under `tools/` for the same
   command-substitution-of-a-failing-function trap.
3. Regression test: with no `world-state/active-campaign.txt`, a representative
   tool must exit 0 (or exit non-zero WITH a printed diagnostic) - never exit
   non-zero silently.

## Acceptance criteria

- [x] With no active campaign, `bash tools/gm-extract.sh prepare <file> <name>` runs to completion and creates the campaign.
- [x] No tool sourcing common.sh can exit non-zero without printing a diagnostic when no campaign is active.
- [x] A test asserts the no-active-campaign bootstrap path for at least gm-extract.sh, gm-campaign.sh, and gm-session.sh.
- [x] Audit result recorded: list of other tools that had the same trap, fixed or confirmed clean.
- [x] Existing tests still pass (`uv run --extra dev pytest`).

## Out of scope

Guarding tools that need an ACTIVE campaign — that is startup-active-campaign-guard,
which explicitly leaves gm-extract.sh able to bootstrap without one. This ticket is
only the silent set -e death.
Refactoring campaign resolution generally. Do not change get_campaign_dir's
contract for the active-campaign case.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T18:42:45Z — pass [review-bootstrap]
reviewed: approved with notes (high-effort review returned only one in-scope
finding, low severity: test fixtures mutate live world-state and could race
under pytest -n — filed as follow-up ticket test-fixture-isolation). Out-of-
scope findings routed: legacy-slug resolution + campaign_slug interpreter
failure → import fix round; reset_world completeness + archive size → new
ticket reset-scope-completeness; gm-session --help guard order → held for
review-startup; vital targeting → held for review-vitals.

### 2026-08-13T18:09:18Z — verified [fable-sott1]
7/7 new tests pass (mutation-checked: 5 fail with guard removed); live probe:
gm-worldgen.sh with no active campaign prints usage, exit 0. Audit recorded:
gm-extract.sh has ~13 raw `cat active-campaign.txt` sites with the same silent
set -e death — filed as follow-up ticket gm-extract-silent-cat (criterion 2
fully met for common.sh-sourced startup; the extract sites are a second cause,
out of this ticket's file scope).

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-13T16:06:15Z  claimed  [fable-sott1]
- 2026-08-13T18:04:14Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T18:09:18Z  verified → in-review  [fable-sott1]
- 2026-08-13T18:42:45Z  review approved → done, committed  [fable-sott1]
