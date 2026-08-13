---
slug: new-game-parity
title: /new-game worlds open with threads, clocks, a start, and rules — like imports do
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: [import-bible-kit-wiring, plot-type-enum-unify]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

enhancement

## What to build

`/new-game` Phase E (new-game.md:151-163) runs only consolidate →
compile-canon → prepare → confirm, while `/import` also runs `spine`,
`seed-clocks`, `seed-opening`, `stat-npcs`, `integrity` (import.md:270-302).
Axis authors write `facts.plot_local/regional/world` and never `plots.json`
(world-author.md:57-60). Result: an authored world starts with no STORY
THREADS, no spine, no clocks, `current_location: null`, and an empty rules
block (nothing writes `campaign_rules`).

1. Extend the world-author contract so axis authors emit structured `plots`
   entries (typed per the unified PLOT_TYPES) alongside facts; merge them in
   `lib/world_author.py`'s consolidation.
2. Run `spine`, `seed-clocks`, and `seed-opening` in Phase E (reusing the
   import-side passes); seed-opening sets `player_position.current_location`.
3. Derive `campaign_rules` from the authored bible via
   `bible_to_campaign_rules` (wired by import-bible-kit-wiring).
4. Restamp `docs/flows/author-a-world.md` (including the five-vs-six phase
   count at :4 and flows/index.md:8) in the same commit.

## Acceptance criteria

- [ ] A scripted /new-game-equivalent fixture run ends with: non-empty `plots.json` (typed), a `story_spine`, at least one seeded threat clock, a non-null starting location, and a non-empty rules block in `gm-session.sh context`.
- [ ] Axis-author merge is race-free (file-ownership fan-out preserved).
- [ ] Import pipeline behavior unchanged (its tests still pass).
- [ ] `docs/flows/author-a-world.md` restamped, phase count corrected.

## Out of scope

Seed/reconcile-report schema validation (a good Tier 2 follow-up), new world
content quality, the world-reconciler agent's checks.

## Verification

Lane: agent

## Blocked by

import-bible-kit-wiring, plot-type-enum-unify

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
