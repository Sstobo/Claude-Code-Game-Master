---
slug: plot-type-enum-unify
title: One PLOT_TYPES enum; stop flattening threat/mystery to side
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T16:06:15Z
changedFiles: [lib/world_stats.py, tools/gm-plot.sh, lib/schemas.py, lib/validators.py, lib/minor_stubs.py, lib/plot_manager.py, lib/session_manager.py, tests/test_minor_stubs.py, tests/test_plot_types.py, docs/schema-reference.md]
resolution: one canonical PLOT_TYPES enum; threat/mystery survive import; all five consumers derive from it
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T18:44:44Z
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

- [x] `grep`-level check: exactly one definition of the plot-type set in lib/; all four former sites import it.
- [x] A `threat` and a `mystery` plot pass through `gm-extract.sh`'s validate step unchanged.
- [x] STORY THREADS ordering test covers all canonical types.
- [x] Full suite passes; the old wrong assertion is gone.
- [x] (review) world_stats.get_counts derives its counter keys from schemas.PLOT_TYPES; summary renders non-zero types.
- [x] (review) gm-plot.sh usage prints the canonical type list (not a hardcoded four).
- [x] (review) schema-reference.md sources: includes /lib/minor_stubs.py.

## Out of scope

The schemas.py-vs-validators.py consolidation decision (Tier 3), plot content
quality, /new-game plot emission (new-game-parity).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T18:44:44Z — pass [review-plots-2]
reviewed: perfect (followup). Note: schema-reference restamp was body+frontmatter,
which the reviewer confirms is OKF-correct for a rewritten body. Commit staged
lib/session_manager.py PARTIALLY (only the three plot-sort hunks) — the
preference-feature hunks in that file belong to another session and remain
uncommitted in the worktree.

### 2026-08-13T18:41:49Z — verified (fix round 1) [fable-sott1]
15/15 targeted tests; gm-plot.sh usage derives all 13 types from schemas;
world_stats counts derive from the enum and hide empty types; schema-reference
claims minor_stubs.py. Implementer full suite 322 passed.

### 2026-08-13T18:39:02Z — fail [review-plots]
reviewed: needs-changes
1. lib/world_stats.py:50-96,250 — fifth consumer hardcodes the old 4-type taxonomy; nine canonical types vanish from the breakdown.
2. tools/gm-plot.sh:23 — usage still lists 4 types.
3. extractor-plots.md schema can't emit threat/mystery — ROUTED to import-extraction-repair's fix round (file ownership).
4. schema-reference.md doesn't claim lib/minor_stubs.py, so synonym-table drift is blind.
Nits: 'other' promoted to accepted type; synonym-table gaps; import-style dual module objects.

### 2026-08-13T18:34:02Z — verified [fable-sott1]
Orchestrator-verified: 12/12 targeted tests pass; exactly one PLOT_TYPE_SORT
definition in lib/; threat/mystery pass validate untouched; unknown types warn
+ fall back to side. Implementer full suite 289 passed. schema-reference.md
restamped (body rewritten). Adjacent find noted on extraction-cap-importance:
extraction_cap.py plot weights rank threat/mystery lowest.

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-13T16:06:15Z  claimed  [fable-sott1]
- 2026-08-13T18:04:14Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T18:34:02Z  verified → in-review  [fable-sott1]
- 2026-08-13T18:39:02Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T18:41:49Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T18:44:44Z  review perfect → done, committed  [fable-sott1]
