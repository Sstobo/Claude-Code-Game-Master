---
slug: fence-disclosures
title: Fences become disclosures — consequences, world-tick, context truncations
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: trust-the-agent
blockedBy: [presence-resolver-unification]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-14T18:52:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md) · split from advisory-fences
(clock magnitude → clock-tick-magnitude; recall cap → recall-top-k)

## Category

enhancement

## What to build

Code currently filters what the GM sees; flip each fence to a disclosure so
the judgment returns to the agent:

1. **consequence_manager.py** — tick returns ALL matches ranked with
   match_reason; the 2-fire limit becomes "fired these 2, N more matched:
   [names]"; last_fired_key becomes an "already fired here" annotation, not a
   suppressor. (Keep the 0.5 fuzzy threshold but surface ≥0.3 near-misses as
   advisory.)
2. **world_tick.py** — apply everything the GM proposes; the cap of 3
   becomes a warning line naming what exceeded it.
3. **session_manager.py context truncations** — every truncation prints its
   remainder ("+4 more threads — gm-plot.sh threads for all"); raise the
   tightest limits (NPC voice lines 2→4, vocab 8→12).

Wait for presence-resolver-unification (this ticket's `blockedBy`) so
`session_manager.py` has a single writer.

## Acceptance criteria

- [ ] A tick with 4 matching consequences reports all 4 (2 fired, 2 disclosed) — test.
- [ ] world-tick applies 5 proposals and warns on the overflow — test.
- [ ] Context output includes remainder counts for every truncated section — test greps "+N more".
- [ ] Full suite passes; living-world.md + scene-context.md restamped where claims move.

## Out of scope

Clock magnitude (clock-tick-magnitude); recall `--top-k` (recall-top-k);
consequence pressure/decay redesign.

## Verification

Lane: agent

## Blocked by

presence-resolver-unification (session_manager.py one-writer chain)

---

## QA Reports

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T18:52:00Z  split advisory-fences → fence-disclosures; blocked → ready; parent trust-the-agent  [gk-t8n2wp]
- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
