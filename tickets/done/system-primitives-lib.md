---
slug: system-primitives-lib
title: World-scoped system primitives in the core
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: world-kit-systems
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T15:42:00Z
changedFiles: [lib/game_core.py, docs/modules/game-core-and-world-kit.md]
resolution: add four pure world-scoped signature-system primitives (named_track, price_roll, reaction_roll, guarded_payoff) to game_core
reviewRounds: 1
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:52:00Z
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

- [x] Ticket contains a design section specifying each primitive's roll, config
      schema, and output before code.
- [x] Four primitives exist in `game_core.py` as pure, deterministic (seedable)
      functions with typed inputs/outputs.
- [x] Each has a runnable self-check / unit assertion covering thresholds and
      edge values (empty track, max track, best/worst roll).
- [x] Primitives contain NO book-specific content (names/thresholds are inputs).
- [x] Existing resolution/harm/progression in `game_core.py` are untouched.

## Out of scope

- Kit instantiation, context surfacing, character moves, lethality (later
  tickets) — this is the library only.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-15T15:52:00Z — pass [reviewer]
reviewed: perfect — boundary logic (both-direction threshold crossing, ladder rung selection, payoff thresholds), clamping at 0/max, and determinism all verified; pure additions (184 ins, 0 del) leave existing resolution/harm/progression untouched; doc honestly states the kit-wiring does not yet exist.
Notes: (non-blocking) `_roll_total` rng-branch parses bare `NdM` only (modifier passed separately per contract); module header present-tense could momentarily read as if the kit layer exists; self-check uses `assert` (stripped under `python -O`, matches repo convention).

### 2026-08-15T15:48:52Z — verified [ss-rt14b]
- Four pure, deterministic, seedable calculators added to `lib/game_core.py`: `named_track`, `price_roll`, `reaction_roll`, `guarded_payoff`. No file I/O (grep-confirmed), all config passed as args, mirroring `spectacle_award`.
- Self-check (`uv run python lib/game_core.py`) passes: exercises empty track, delta-past-max clamp + at_max, downward crossing + floor clamp, best/worst price rung, both reaction extremes, all three guarded_payoff outcomes, same-seed determinism.
- `tests/test_game_core.py` still green (no regression to existing resolution/spectacle code).
- Design note: reuses the repo dice path; determinism via injected `rng` (`random.Random`). Severity subtracts from the price total; selectors clamp to the worst rung below all thresholds.

## History

- 2026-08-15T15:52:00Z  review perfect → done + committed  [ss-rt14b]
- 2026-08-15T15:48:52Z  verified → in-review  [ss-rt14b]
- 2026-08-15T15:42:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T15:42:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
