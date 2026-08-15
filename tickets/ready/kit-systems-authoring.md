---
slug: kit-systems-authoring
title: Kit instantiates + names 1-3 systems; surfaced in context
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: world-kit-systems
blockedBy: [system-primitives-lib]
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

Let a World Kit turn the primitives into named, world-specific systems, and make
the GM see and roll them.

- `world_kit.py` / `ruleset.json` gains a `systems` block: a list of
  `{primitive, name, config}` instantiations. Legacy free-text
  `signature_systems` stays as flavor beside it.
- `/import` and `/new-game` pick 1–3 primitives fitting the world's tone/themes
  and name them (import can infer from extracted themes; new-game from tone).
- Scene context (`gm-session.sh context`) emits the active kit's `systems` —
  name, current track values, and when each fires — alongside YOUR WORLD'S RULES.
- CLAUDE.md / relevant skill guidance tells the GM to roll these systems, not
  honor them by vibes.

## Acceptance criteria

- [ ] `world_kit.py` persists and round-trips a `systems` list of
      `{primitive, name, config}`.
- [ ] `/import` and `/new-game` produce a kit with 1–3 named systems appropriate
      to the world.
- [ ] `gm-session.sh context` emits the instantiated systems block with names and
      live track values.
- [ ] Guidance instructs the GM to roll the systems (references the primitives).
- [ ] A kit with no `systems` still loads (backward compatible).

## Out of scope

- The primitive implementations themselves (blocker ticket).
- Lethality dial and PC signature move (separate tickets).

## Verification

Lane: agent

## Blocked by

system-primitives-lib

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
