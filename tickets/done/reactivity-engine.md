---
slug: reactivity-engine
title: check_pending fires + expires triggers (hybrid structured + scored fuzzy)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [structured-trigger-schema]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:28:15Z
changedFiles: [lib/consequence_manager.py, tests/test_reactivity_engine.py]
resolution: check_pending(world_state) evaluates triggers and returns only fired consequences (match_reason, capped, sorted); structured matched by type, legacy scored fuzzily; expired auto-archived; no-arg call stays the legacy accessor
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:28:15Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Give the "living world" an actual engine. Today `check_pending` (consequence_
manager.py:~62) returns the entire `active[]` list forever with zero evaluation.
Rewrite it to evaluate triggers against current world state (location, present
NPCs, game-time, recent events) and return ONLY fired consequences — auto-aging
or auto-resolving them, archiving expired ones. Structured triggers match
exactly; free-text triggers get a scored fuzzy match instead of a raw dump. Cap
output to the most relevant.

## Acceptance criteria

- [x] `check_pending(world_state)` returns only consequences whose trigger matches current state.
- [x] Structured triggers evaluated by type; free-text triggers scored and ranked, not dumped wholesale.
- [x] Expired consequences (past `expiry`) auto-archived to `resolved`/expired, not surfaced.
- [x] Result capped (e.g. top 1-2) with each item carrying its match reason.
- [x] PROTECT: never silently drops a consequence without archiving it; `active[]` stops growing into a stale wall.
- [x] Tests: a trigger fires when its location/npc/time condition is met and stays silent otherwise (DCC fixture).

## Verification

Lane: agent

## Blocked by

structured-trigger-schema

---

## QA Reports

### 2026-06-06T04:28:15Z — pass [ss-tix001]
`uv run pytest` → 40 passed (7 new in tests/test_reactivity_engine.py).
- check_pending(world_state, limit=2): evaluates each active consequence via _evaluate_trigger (structured on_location/on_npc/on_time/on_event = score 1.0 + reason; legacy free-text = word-overlap score, fires at >=0.5) and _is_expired (expiry substring in world text). Expired items are moved to resolved and persisted; fired items annotated with match_reason, sorted by score, capped at limit. Firing does NOT remove (DM vetoes/resolves; tick dedups).
- check_pending() with no world_state returns the raw active list (backward compat; the test-harness characterization still passes).
- Tests cover each trigger type firing, silence on no-match, the cap, and expiry → archived (not fired, removed from active, present in resolved).
- world_state keys: location, present_npcs, time, events, date. reactivity-tick-wiring (next) builds this from session state and wires it into move/time.

## History

- 2026-06-06T04:28:15Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:28:15Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
