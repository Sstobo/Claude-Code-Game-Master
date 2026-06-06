---
slug: between-session-worldtick
title: Constrained between-session world tick (off-screen developments)
category: enhancement
kind: hitl
priority: p2
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [reactivity-tick-wiring, longterm-memory]
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

Make the world keep living when the player looks away. On session end/start, a
world-builder pass advances 1-3 SMALL off-screen developments tied to game-time
and writes them as new consequences/plot events, grounded in source RAG +
existing plots. Off-screen changes must stay small, reversible, and canon-
grounded to avoid contradicting the book — so it ships with the provenance log +
rollback and needs human review (hitl). Respect tone (cozy worlds tick gently).

## Acceptance criteria

- [ ] On session end/start, 1-3 bounded off-screen developments are generated and written as consequences/plot events.
- [ ] Developments are grounded in source RAG + existing plots (no free-floating invention).
- [ ] Each tick is logged via the provenance system and is rollback-able.
- [ ] A cap + tone setting prevents runaway or jarring off-screen change.
- [ ] Human review confirms a generated tick feels consequential without contradicting canon.

## Verification

Lane: manual

## Blocked by

reactivity-tick-wiring, longterm-memory

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
