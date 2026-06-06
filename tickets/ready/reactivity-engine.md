---
slug: reactivity-engine
title: check_pending fires + expires triggers (hybrid structured + scored fuzzy)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [structured-trigger-schema]
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

Give the "living world" an actual engine. Today `check_pending` (consequence_
manager.py:~62) returns the entire `active[]` list forever with zero evaluation.
Rewrite it to evaluate triggers against current world state (location, present
NPCs, game-time, recent events) and return ONLY fired consequences — auto-aging
or auto-resolving them, archiving expired ones. Structured triggers match
exactly; free-text triggers get a scored fuzzy match instead of a raw dump. Cap
output to the most relevant.

## Acceptance criteria

- [ ] `check_pending(world_state)` returns only consequences whose trigger matches current state.
- [ ] Structured triggers evaluated by type; free-text triggers scored and ranked, not dumped wholesale.
- [ ] Expired consequences (past `expiry`) auto-archived to `resolved`/expired, not surfaced.
- [ ] Result capped (e.g. top 1-2) with each item carrying its match reason.
- [ ] PROTECT: never silently drops a consequence without archiving it; `active[]` stops growing into a stale wall.
- [ ] Tests: a trigger fires when its location/npc/time condition is met and stays silent otherwise (DCC fixture).

## Verification

Lane: agent

## Blocked by

structured-trigger-schema

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
