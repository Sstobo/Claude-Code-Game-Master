---
slug: plot-type-enum-unify
title: One PLOT_TYPES enum; stop flattening threat/mystery to side
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Four incompatible plot-type enums exist: lib/schemas.py:15,
lib/validators.py:208, lib/minor_stubs.py:20, lib/plot_manager.py:303 (plus
the sort order at lib/session_manager.py:737). The post-import pass
`minor_stubs.validate_plot_types` (lib/minor_stubs.py:64-66, invoked from
tools/gm-extract.sh:588) rewrites any off-enum type to `"side"` — so every
`threat` and `mystery` plot an import produces is flattened before STORY
THREADS (which sorts main → threat → mystery → side) can ever see it.
`tests/test_minor_stubs.py` asserts the wrong enum and locks the bug in.

1. Define one `PLOT_TYPES` constant (and the display sort order) in
   `lib/schemas.py`; import it in validators, minor_stubs, plot_manager, and
   session_manager.
2. `validate_plot_types` maps off-enum values to the nearest legal type
   (documented mapping) instead of flattening everything to `side`; `threat`
   and `mystery` are legal and pass through untouched.
3. Fix `tests/test_minor_stubs.py`; add a test that a plot list containing
   threat/mystery survives the post-import pass with types intact.

## Acceptance criteria

- [ ] `grep`-level check: exactly one definition of the plot-type set in lib/; all four former sites import it.
- [ ] A `threat` and a `mystery` plot pass through `gm-extract.sh`'s validate step unchanged.
- [ ] STORY THREADS ordering test covers all canonical types.
- [ ] Full suite passes; the old wrong assertion is gone.

## Out of scope

The schemas.py-vs-validators.py consolidation decision (Tier 3), plot content
quality, /new-game plot emission (new-game-parity).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
