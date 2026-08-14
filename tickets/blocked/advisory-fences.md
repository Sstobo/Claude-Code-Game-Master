---
slug: advisory-fences
title: Fences become disclosures — consequences, world-tick, truncations, clocks, recall
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: [core-prompt-detox]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T21:30:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md) · Trust the Agent review (artifact 1a6acb14)

## Category

enhancement

## What to build

Code currently filters what the GM sees; flip each fence to a disclosure so
the judgment returns to the agent:

1. **consequence_manager.py:178,206** — tick returns ALL matches ranked with
   match_reason; the 2-fire limit becomes "fired these 2, N more matched:
   [names]"; last_fired_key becomes an "already fired here" annotation, not a
   suppressor. (Keep the 0.5 fuzzy threshold but surface ≥0.3 near-misses as
   advisory.)
2. **world_tick.py:27,32** — apply everything the GM proposes; the cap of 3
   becomes a warning line naming what exceeded it.
3. **session_manager.py context truncations** (:531-851) — every truncation
   prints its remainder ("+4 more threads — gm-plot.sh threads for all");
   raise the tightest limits (NPC voice lines 2→4, vocab 8→12).
4. **gm-time.sh:23 + threat_clocks.py** — accept elapsed magnitude
   (`--ticks N` or derived from a duration arg) so three weeks ≠ ten minutes.
5. **campaign_memory.py:132 + gm-recall.sh** — expose `--top-k` (default
   raised to 5).

COLLISION NOTE: session_manager.py — same caveat as core-prompt-detox
(blocker declared) plus any other in-flight claim on that file.

## Acceptance criteria

- [ ] A tick with 4 matching consequences reports all 4 (2 fired, 2 disclosed) — test.
- [ ] world-tick applies 5 proposals and warns on the overflow — test.
- [ ] Context output includes remainder counts for every truncated section — test greps "+N more".
- [ ] gm-time.sh advance of a multi-day duration ticks clocks proportionally — test.
- [ ] gm-recall.sh --top-k 8 returns 8 — test.
- [ ] Full suite passes; living-world.md + scene-context.md restamped where claims move.

## Out of scope

Consequence pressure/decay redesign (ideas list); relative-time verb itself
(T2.3 owns `advance`); memory working-set redesign.

## Verification

Lane: agent

## Blocked by

core-prompt-detox

---

## QA Reports

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
