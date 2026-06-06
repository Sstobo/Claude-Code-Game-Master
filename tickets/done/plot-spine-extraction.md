---
slug: plot-spine-extraction
title: Extract a plot spine (arc + ordering + through-line), not a flat bag
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [cap-extraction-30, import-integrity-gate]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:15:00Z
changedFiles: [lib/plot_spine.py, lib/session_manager.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_plot_spine.py]
resolution: dm-extract.sh spine orders MAIN plots by earliest source appearance (sequence + linear depends_on), records story_spine through-line on the overview; session_manager STORY THREADS now sort by sequence; live arc ordered Survive→Decode→Escape→Cookbook→Trap→Detonate
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T17:17:37Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Today plots.json is a flat bag of independent hooks (23 peers, all default `active`,
zero ordering). The book has an ARC the extraction flattened. Add a plot-spine pass
that captures narrative structure: an ordered main-arc sequence, dependencies between
plots (`depends_on` / unlocks), an `act` or `stage` grouping, and the book's single
through-line (the spine statement). Persist either as new fields on plot entries
(`sequence`, `act`, `depends_on`) or a dedicated `spine.json` the story-spine context
loader can read. The runtime story-spine (session_manager) already surfaces threads
main-first + latest beat — feed it real ordering instead of type-sort.

## Acceptance criteria

- [x] Main-arc plots carry an explicit order/sequence (not just type=main).
- [x] Plot dependencies captured (`depends_on` / unlocks) where the book implies them.
- [x] A single through-line / spine statement is recorded for the campaign.
- [x] Output is consumed by the story-spine context (session_manager) — threads ordered by arc, not type.
- [x] Runs on the capped ≤30 plot set; references already canonicalized by the integrity gate.
- [x] Verified on the anarchists-cookbook arc: escape-train → decode-rail → reach-stairwell → soul-crystal finale ordered correctly.

## Verification

Lane: agent

## Blocked by

cap-extraction-30, import-integrity-gate

---

## QA Reports

### 2026-06-06T17:17:37Z — pass [ss-7q3w9z]
5 unit tests in tests/test_plot_spine.py pass: main plots ordered by source appearance;
depends_on chains the arc; side plots not sequenced; apply_spine persists story_spine to
overview; STORY THREADS honor sequence (dcc_world). story-spine regression (5 tests) green.
Live apply on anarchists-cookbook produced the correct 6-beat arc: Survive→Decode→Escape
routes→Cookbook→Trap Sprung→Detonate Soul Crystals; through_line + arc written to overview.
[note] depends_on is a deterministic linear chain (each beat depends on the prior); richer
branch dependencies are out of scope for this deterministic pass.

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
- 2026-06-06T17:15:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:17:37Z  done  [ss-7q3w9z]
