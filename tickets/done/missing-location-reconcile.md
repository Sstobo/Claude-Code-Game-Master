---
slug: missing-location-reconcile
title: Reconcile referenced-but-missing locations
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [cap-extraction-30, import-integrity-gate]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:05:00Z
changedFiles: [lib/location_reconcile.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_location_reconcile.py]
resolution: dm-extract.sh reconcile stubs (name + RAG passage + bidirectional hub link) or drops unresolved location refs in plots/tags/connections; full chain takes location-kind unresolved to 0 (cap→reconcile→integrity); runs before the integrity gate
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:08:08Z
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

- [x] After reconcile, every plot/tag/connection location reference resolves to a node.
- [x] Stub nodes carry a name, ≥1 source passage, and ≥1 bidirectional connection (no orphans).
- [x] Frequently-referenced missing stations get real stubs, not silent drops.
- [x] Runs before the import-integrity-gate's final fail check (so reconciled refs pass).
- [x] Reconcile actions (stubbed vs rewritten vs dropped) are reported.

## Verification

Lane: agent

## Blocked by

cap-extraction-30, import-integrity-gate

---

## QA Reports

### 2026-06-06T17:08:08Z — pass [ss-7q3w9z]
6 unit tests in tests/test_location_reconcile.py pass: stubbable heuristic; missing plot
location stubbed + bidirectionally linked to hub; descriptive phrase ("Skull Empire /
dungeon (location unknown)") dropped not stubbed; existing ref kept via alias; dead
connection edge pruned; run_reconcile writes files. Full-chain smoke on real-data copy
(cap→reconcile→integrity): location-kind unresolved 176→0 (58 stubbed, 13 phrases dropped,
225 kept). Stub nodes carry hub link + RAG passage (when vectors present).
[handoff] The 44 remaining unresolved are ALL plot.npcs — plot-referenced NPCs the hard
30-cap couldn't keep (>30 are referenced). NPC-ref reconciliation is minor-entity-stubs-
taxonomy's scope; the strict integrity gate will pass once that ships.

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:05:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:08:08Z  done  [ss-7q3w9z]
