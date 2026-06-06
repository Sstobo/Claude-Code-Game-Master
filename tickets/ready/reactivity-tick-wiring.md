---
slug: reactivity-tick-wiring
title: Wire a reactivity tick into move/time; surface 1-2 fired per beat
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [reactivity-engine]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
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

- [ ] Moving (`dm-session.sh move`) and advancing time (`dm-time.sh`) run the reactivity tick automatically.
- [ ] Fired consequences (max 1-2/beat) surface with their match reason in the DM-visible output.
- [ ] DM can veto/defer a fired consequence without it being lost (stays active or re-armed).
- [ ] No duplicate firing of the same consequence on consecutive ticks unless re-armed.
- [ ] Test: a move into the matching location fires the right consequence exactly once via the wired path.

## Verification

Lane: agent

## Blocked by

reactivity-engine

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
