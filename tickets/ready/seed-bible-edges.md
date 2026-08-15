---
slug: seed-bible-edges
title: Wire 2-4 faction/geography edges at creation
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: living-world
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

Living World (prds/living-world.md)

## Category

enhancement

## What to build

The world-bible's `factions` and `geography` graphs ship with `edges: []` — a
cast list, not a world. Seed a few real tensions at creation so the GM can pull
on an existing relationship instead of inventing one.

- The bible builder writes 2–4 `edges` into the faction and/or geography graphs
  at creation (import grounds them in the source; new-game authors from themes).
- Edges name a relationship/tension between two existing nodes.

## Acceptance criteria

- [ ] After creation, the bible's faction and/or geography graphs contain 2–4
      edges connecting existing nodes with a named tension/relationship.
- [ ] Edges reference only nodes that exist in the same graph.
- [ ] Import-seeded edges are grounded in the source; new-game edges fit the
      stated themes.
- [ ] Empty-graph worlds (no nodes) don't error — they simply seed no edges.

## Out of scope

- A full relationship map / faction simulation — a few seed edges only.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
