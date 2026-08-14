---
slug: prepare-anchor-fallback
title: prepare's CALLER_PWD anchor disagrees with tool-emitted project-root-relative paths
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T14:50:33Z
changedFiles: [lib/agent_extractor.py, tools/gm-extract.sh, tests/test_wrapper_cwd_anchoring.py, docs/conventions/tool-wrapper-contract.md]
resolution: prepare resolves both anchors; the world-state pin is real for extraction; live tree provably untouched
reviewRounds: 2
implementer: null
createdAt: 2026-08-14T14:55:00Z
updatedAt: 2026-08-14T15:23:49Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Post-commit finding on wrapper-cwd-anchoring (17e6f6b): every wrapper now runs
at PROJECT_ROOT, so tool-EMITTED relative paths are project-root-relative
(world_author.compile_canon returns world-state/campaigns/<n>/authored-canon.md),
but gm-extract.sh `prepare` resolves relatives against CALLER_PWD. The
documented /new-game pipe (new-game.md:157-161: compile-canon --json → prepare
"$CANON") therefore breaks from any cwd but the repo root — exactly the
subagent case the cd fix was for.

1. tools/gm-extract.sh prepare_document: try "$CALLER_PWD/$document" first,
   fall back to "$PROJECT_ROOT/$document", only then error (user-typed paths
   keep caller anchoring; tool-emitted paths resolve too).
2. Test hardening from the same review: the decoy test needs the
   skipif+pointer-guard pattern (it can mkdir world-state/ on a fresh clone
   and reads the live tree); the decoy assertion and the 14-wrapper sweep
   need returncode assertions (currently pass green on total failure).

## Acceptance criteria

- [x] From a foreign cwd, prepare accepts both a caller-relative path and a project-root-relative path (both test-pinned); a missing path still errors.
- [x] The /new-game pipe shape (compile-canon output → prepare) works from a foreign cwd — test simulates it.
- [x] Decoy test guarded like its persist-file predecessor; both cwd tests assert returncode.
- [x] Full suite passes.

## Out of scope

Python-side default-path refactor; other wrappers.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T15:23:49Z — pass [review-anchor-2]
reviewed: perfect (round 2; revert experiment proved the pin and the
teardown guard both bind). Orchestrator applied the reviewer's optional
doc polish (naming AgentExtractor in the bypass clause). Notes recorded:
take_flag dangling-flag edge unreachable from the wrapper; snapshot is
names-only; SIGKILL can strand a scratch dir (cosmetic).

### 2026-08-14T15:15:48Z — verified (fix round 1) [fable-sott1]
20/20 anchoring tests; live tree holds only conan post-run (verified);
--world-state now flows to all four agent_extractor verbs (pin is real);
tie order pinned; genuine forward pipe-shape path; contract doc carries the
manager-side seam rule. Implementer full suite 552 passed.

### 2026-08-14T15:06:21Z — fail [review-anchor]
reviewed: needs-changes
1. (must) prepare leaks full campaigns into the LIVE world-state: agent_extractor
defaults to relative 'world-state' and prepare passes no --world-state; the test
docstring claims a pin it doesn't have. Reviewer cleaned two residue campaigns.
2. Tie case (both anchors) untested though correct.
3. Pipe-shape docstring overclaims (climb-out relpath, not the forward shape).
4. Module docstring still describes the single-anchor rule.
Confirmed: fix necessary and correct; sweep rows real; restamp truthful.

### 2026-08-14T14:59:33Z — verified [fable-sott1]
19/19 anchoring tests; two-anchor resolution mutation-checked (reverted
gm-extract fails exactly the new test); sweep returncodes asserted with an
EMPTY allowlist — two vacuous rows fixed instead of excused; decoy test
guarded + positive-asserted. Implementer full suite 546 passed.

## History

- 2026-08-14T14:55:00Z  created → ready (stray-fork review post-commit findings)  [fable-sott1]
- 2026-08-14T14:50:33Z  claimed  [fable-sott1]
- 2026-08-14T14:54:08Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T14:59:33Z  verified → in-review  [fable-sott1]
- 2026-08-14T15:06:21Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-14T15:15:48Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-14T15:23:49Z  review perfect → done, committed  [fable-sott1]
