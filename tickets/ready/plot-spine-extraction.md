---
slug: plot-spine-extraction
title: Extract a plot spine (arc + ordering + through-line), not a flat bag
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [cap-extraction-30, import-integrity-gate]
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T16:47:47Z
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

- [ ] Main-arc plots carry an explicit order/sequence (not just type=main).
- [ ] Plot dependencies captured (`depends_on` / unlocks) where the book implies them.
- [ ] A single through-line / spine statement is recorded for the campaign.
- [ ] Output is consumed by the story-spine context (session_manager) — threads ordered by arc, not type.
- [ ] Runs on the capped ≤30 plot set; references already canonicalized by the integrity gate.
- [ ] Verified on the anarchists-cookbook arc: escape-train → decode-rail → reach-stairwell → soul-crystal finale ordered correctly.

## Verification

Lane: agent

## Blocked by

cap-extraction-30, import-integrity-gate

---

## QA Reports

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
