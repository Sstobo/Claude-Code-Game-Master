---
slug: prepare-anchor-fallback
title: prepare's CALLER_PWD anchor disagrees with tool-emitted project-root-relative paths
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-14T14:55:00Z
updatedAt: 2026-08-14T14:55:00Z
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

- [ ] From a foreign cwd, prepare accepts both a caller-relative path and a project-root-relative path (both test-pinned); a missing path still errors.
- [ ] The /new-game pipe shape (compile-canon output → prepare) works from a foreign cwd — test simulates it.
- [ ] Decoy test guarded like its persist-file predecessor; both cwd tests assert returncode.
- [ ] Full suite passes.

## Out of scope

Python-side default-path refactor; other wrappers.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-14T14:55:00Z  created → ready (stray-fork review post-commit findings)  [fable-sott1]
