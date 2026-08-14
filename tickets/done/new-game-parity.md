---
slug: new-game-parity
title: /new-game worlds open with threads, clocks, a start, and rules — like imports do
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: [import-bible-kit-wiring, plot-type-enum-unify]
claimedBy: fable-sott1
claimedAt: 2026-08-14T13:13:08Z
changedFiles: [lib/world_author.py, '.claude/agents/world-author.md', '.claude/commands/new-game.md', docs/flows/author-a-world.md, docs/flows/index.md, tests/test_new_game_parity.py]
resolution: authored worlds open alive — typed plots, spine, clocks, a start, and derived rules
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T13:38:59Z
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

- [x] A scripted /new-game-equivalent fixture run ends with: non-empty `plots.json` (typed), a `story_spine`, at least one seeded threat clock, a non-null starting location, and a non-empty rules block in `gm-session.sh context`.
- [x] Axis-author merge is race-free (file-ownership fan-out preserved).
- [x] Import pipeline behavior unchanged (its tests still pass).
- [x] `docs/flows/author-a-world.md` restamped, phase count corrected.

## Out of scope

Seed/reconcile-report schema validation (a good Tier 2 follow-up), new world
content quality, the world-reconciler agent's checks.

## Verification

Lane: agent

## Blocked by

import-bible-kit-wiring, plot-type-enum-unify

---

## QA Reports

### 2026-08-14T13:38:59Z — pass [review-parity]
reviewed: perfect. Advisories filed as reconciler-plots-awareness ticket:
world-reconciler's never-edit list + cross-link check don't know plots.json;
authored type aliases (e.g. 'conflict') reach /world-check unmapped since
Phase E lacks import's normalize pass. set -e line noted as decorative —
the honest STOP prose does the work.

### 2026-08-14T13:32:47Z — verified [fable-sott1]
4/4 parity tests: typed plots merge (existing-wins dedupe, never clobbered
empty), full chain yields spine + 9-segment threat clock + non-null start +
campaign_rules. Phase-count error fixed via doc + regenerated index. Import
tests green. Implementer full suite 505 passed.

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T13:13:08Z  claimed  [fable-sott1]
- 2026-08-14T13:21:01Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T13:32:47Z  verified → in-review  [fable-sott1]
- 2026-08-14T13:38:59Z  review perfect → done, committed  [fable-sott1]
