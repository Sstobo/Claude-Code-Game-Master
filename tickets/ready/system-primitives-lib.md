---
slug: system-primitives-lib
title: World-scoped system primitives in the core
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: world-kit-systems
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
---

## Parent

World-Kit Systems (prds/world-kit-systems.md)

## Category

enhancement

## What to build

The primitive layer: four world-agnostic, dice-backed mechanical building blocks
in `game_core.py`, each a small deterministic function with typed in/out. These
are the executable substrate a kit skins per world.

**Design-first:** open the ticket with a short spec of each primitive's roll
shape, config schema, and consequence output before implementing.

- **Named Track** — a meter (name, max, thresholds); advance/relieve; returns the
  threshold consequence(s) crossed.
- **Price Roll** — given an action's severity, roll a cost on a ladder; return the
  cost outcome.
- **Reaction Roll** — roll an NPC disposition modified by a track/reputation
  value; return the reaction tier.
- **Guarded / Cursed Payoff** — roll before a marked treasure is taken; return
  clean / guardian-wakes / curse-attaches.

## Acceptance criteria

- [ ] Ticket contains a design section specifying each primitive's roll, config
      schema, and output before code.
- [ ] Four primitives exist in `game_core.py` as pure, deterministic (seedable)
      functions with typed inputs/outputs.
- [ ] Each has a runnable self-check / unit assertion covering thresholds and
      edge values (empty track, max track, best/worst roll).
- [ ] Primitives contain NO book-specific content (names/thresholds are inputs).
- [ ] Existing resolution/harm/progression in `game_core.py` are untouched.

## Out of scope

- Kit instantiation, context surfacing, character moves, lethality (later
  tickets) — this is the library only.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
