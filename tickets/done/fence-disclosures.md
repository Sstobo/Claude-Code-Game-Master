---
slug: fence-disclosures
title: Fences become disclosures — consequences, world-tick, context truncations
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: trust-the-agent
blockedBy: [presence-resolver-unification]
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T20:09:48Z
changedFiles: [lib/consequence_manager.py, lib/world_tick.py, lib/session_manager.py, tests/test_fence_disclosures.py, tests/test_reactivity_tick.py, tests/test_world_tick.py, tests/test_reactivity_engine.py, docs/modules/living-world.md, docs/modules/scene-context.md, docs/log.md]
resolution: tick fires 2 and discloses rest; world-tick applies all + warns; context prints +N more
reviewRounds: 1
implementer: 5ee8d292-8a77-49a2-b384-88636b7d2190
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-14T20:30:00Z
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

- [x] A tick with 4 matching consequences reports all 4 (2 fired, 2 disclosed) — test.
- [x] world-tick applies 5 proposals and warns on the overflow — test.
- [x] Context output includes remainder counts for every truncated section — test greps "+N more".
- [x] Full suite passes; living-world.md + scene-context.md restamped where claims move.

## Out of scope

Clock magnitude (clock-tick-magnitude); recall `--top-k` (recall-top-k);
consequence pressure/decay redesign.

## Verification

Lane: agent

## Blocked by

presence-resolver-unification (session_manager.py one-writer chain)

---

## QA Reports

### 2026-08-14T20:30:00Z — reviewed perfect [cba74fc5]
No correctness/regression findings. Nits: `test_cap_is_enforced` name; `fired these 0` header; last_overflow survives a failed log rollback; voice remainder re-counts context. New-criteria leftover: CLAUDE.md / gm-session.sh still say world-tick is capped 1–3.

### 2026-08-14T20:20:00Z — verified [gk-t8n2wp]
Tick fires 2 / discloses rest; already-fired annotates; world-tick applies 5 and warns overflow; context greps +N more (threads/facts/voice/vocab/sessions/pending/passages). Updated test_reactivity_engine check_pending cap. pytest fence_disclosures + reactivity_tick + world_tick + reactivity_engine + provenance + check_pending + structured_triggers + get_full_context + presence_resolver + untruncate_rules + voice_surfacing + lean_core: 64 passed.

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T20:30:00Z  reviewed perfect → done  [gk-t8n2wp]
- 2026-08-14T20:20:00Z  verified → in-review, review dispatched  [gk-t8n2wp]
- 2026-08-14T20:09:48Z  claimed; doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  split advisory-fences → fence-disclosures; blocked → ready; parent trust-the-agent  [gk-t8n2wp]
- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
