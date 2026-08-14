---
slug: reconciler-plots-awareness
title: world-reconciler and Phase E don't know plots.json exists
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-14T13:40:00Z
updatedAt: 2026-08-14T13:40:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

enhancement

## What to build

From review-parity's advisories on new-game-parity:
1. .claude/agents/world-reconciler.md:70 — the "consolidation owns those,
   NEVER edit" list omits plots.json (now consolidation-owned); the check-3
   cross-link section has no notion of the authored `plots` key, so a plot
   naming an unauthored location stays dangling and opening_seed silently
   falls back to the hub. Two one-line prompt edits.
2. Phase E parity gap: import runs the plot-type alias normalization
   (minor_stubs synonyms) — /new-game does not, so an authored
   "type": "conflict" reaches /world-check as an error instead of mapping to
   threat. Add the normalize call (or a validate-plot-types pass) to Phase E.
3. (optional) new-game.md:171's decorative set -e line — drop or make honest.

## Acceptance criteria

- [ ] Reconciler prompt names plots.json in both places.
- [ ] An authored "conflict" plot lands as threat by the end of Phase E (test at the world_author/minor_stubs level).
- [ ] Full suite passes.

## Out of scope

Reconciler check redesign; seed schema validation.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-14T13:40:00Z  created → ready (review-parity advisories)  [fable-sott1]
