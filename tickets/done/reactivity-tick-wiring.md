---
slug: reactivity-tick-wiring
title: Wire a reactivity tick into move/time; surface 1-2 fired per beat
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [reactivity-engine]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:31:47Z
changedFiles: [lib/consequence_manager.py, tools/dm-session.sh, tools/dm-time.sh, tools/dm-consequence.sh, tests/test_reactivity_tick.py]
resolution: tick()/tick_from_session() fire matching consequences once per scene (dedup via last_fired_key, re-arm on scene change); wired into dm-session.sh move and dm-time.sh; dm-consequence.sh tick surfaces fired items with reason + veto hint
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:31:47Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Make firing automatic, not eyeballed. Wire a `dm-consequence.sh tick` (or
in-process call) into the move + time-advance flow so the reactivity engine runs
after every location change / time jump. Surface at most 1-2 fired consequences
per beat WITH the trigger reason so the DM can veto for dramatic timing. Output
flows into the session context the DM reads.

## Acceptance criteria

- [x] Moving (`dm-session.sh move`) and advancing time (`dm-time.sh`) run the reactivity tick automatically.
- [x] Fired consequences (max 1-2/beat) surface with their match reason in the DM-visible output.
- [x] DM can veto/defer a fired consequence without it being lost (stays active or re-armed).
- [x] No duplicate firing of the same consequence on consecutive ticks unless re-armed.
- [x] Test: a move into the matching location fires the right consequence exactly once via the wired path.

## Verification

Lane: agent

## Blocked by

reactivity-engine

---

## QA Reports

### 2026-06-06T04:31:47Z — pass [ss-tix001]
`uv run pytest` → 44 passed (4 new in tests/test_reactivity_tick.py); `bash -n` ok on dm-session/dm-time/dm-consequence.
- consequence_manager.tick(world_state) fires matching consequences once per context key (location|time|date) via last_fired_key; re-arms on scene change; archives expired; caps at limit; returns match_reason. tick_from_session() builds world_state from campaign-overview (location/time/date) + present NPCs (party + location-tagged).
- CLI `tick` + dm-consequence.sh `tick` print fired items with "↳ fired because: <reason> (veto if the timing's wrong)". dm-session.sh move now runs the tick (replacing the old dump of all pending); dm-time.sh runs it after advancing time (on_time triggers like nightfall/deadlines).
- Live: `dm-consequence.sh tick` on DCC at Warehouse/day → "(nothing triggered here)" — correct, no active trigger matches.
- Tests: fire-then-dedup same scene, re-arm on scene change, cap, tick_from_session runs against campaign state.

## History

- 2026-06-06T04:31:47Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:31:47Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
