---
slug: generic-core
title: Thin generic resolution core (d20-vs-DC + harm/conditions + progression)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [test-harness-scaffold]
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

The system-agnostic core every world runs on, with NO D&D 5e assumptions. A thin
core providing: the d20-vs-DC resolution mechanic (reuse `dice.py` + the DC
ladder), a generic contest/opposed-check primitive, abstract HP/harm + conditions
primitives, and three configurable progression frameworks — `milestone`
(default), `resource-axis`, `xp-levels` — selected/configured by a kit. Stat
names, combat feel, and progression specifics stay OUT of core (they're bespoke
per book). PROTECT `dice.py` as the deterministic RNG.

## Acceptance criteria

- [ ] A `core` module exposes: resolve_check(modifier, dc), opposed_check(a, b), apply_harm/heal (abstract HP), add/remove condition.
- [ ] Three progression strategies implemented behind one interface: milestone, resource-axis, xp-levels; none hardcoded as the only path.
- [ ] Zero D&D-5e-specific symbols in core (no six-ability requirement, no level-20 cap, no spell slots).
- [ ] `dice.py` reused unchanged as the RNG; advantage/disadvantage still honored.
- [ ] Unit tests cover each progression framework + resolution/contest/harm primitives.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
