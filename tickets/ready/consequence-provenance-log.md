---
slug: consequence-provenance-log
title: Provenance log + per-beat snapshot for reactive firing
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

Reactive-safety net (red-team requirement). Once consequences fire on their own,
a bad trigger or misfire can contradict canon or railroad the player. Add a
"why did this fire" provenance log entry per firing (consequence id, trigger
reason, world-state snapshot ref, timestamp) and a lightweight per-beat snapshot
so a misfire is debuggable and undoable via the existing atomic save/restore.

## Acceptance criteria

- [ ] Each fired consequence writes a provenance record (id, reason, matched condition, timestamp).
- [ ] A per-beat snapshot (or reuse of atomic save) lets the dev roll back one reactive beat.
- [ ] Provenance is queryable (`dm-consequence.sh log` or similar) without parsing prose.
- [ ] Rollback restores consequence + world state to pre-fire without corrupting other state.
- [ ] Test: fire → inspect provenance → rollback → state matches pre-fire snapshot.

## Verification

Lane: agent

## Blocked by

reactivity-engine

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
