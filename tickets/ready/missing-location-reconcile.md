---
slug: missing-location-reconcile
title: Reconcile referenced-but-missing locations
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [cap-extraction-30, import-integrity-gate]
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Plots + NPC tags depend on locations never extracted as nodes (stairwell stations
24/36/48/72, Station 101, Royal Palace ×7 tags, etc.). With the top-30 cap this gets
worse. In the integrity pass: collect every location named in plot.locations /
npc.location_tags / connection.to that lacks a node, then either (a) rewrite it to
the nearest canonical key via the alias normalizer, or (b) create a lightweight stub
node (name + one source passage + at least one bidirectional connection). Mechanically
central, repeatedly-named places get real stubs; one-off descriptive phrases get
rewritten or dropped from refs.

## Acceptance criteria

- [ ] After reconcile, every plot/tag/connection location reference resolves to a node.
- [ ] Stub nodes carry a name, ≥1 source passage, and ≥1 bidirectional connection (no orphans).
- [ ] Frequently-referenced missing stations get real stubs, not silent drops.
- [ ] Runs before the import-integrity-gate's final fail check (so reconciled refs pass).
- [ ] Reconcile actions (stubbed vs rewritten vs dropped) are reported.

## Verification

Lane: agent

## Blocked by

cap-extraction-30, import-integrity-gate

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
