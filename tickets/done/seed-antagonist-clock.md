---
slug: seed-antagonist-clock
title: Every new campaign ships with an off-screen antagonist clock
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: living-world
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:18:00Z
changedFiles: [.claude/commands/import.md, .claude/commands/new-game.md]
resolution: import/new-game seed >=1 antagonist threat clock at creation (gm-clock.sh add, off-screen aim) so every campaign ships with a spine
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:18:00Z
---

## Parent

Living World (prds/living-world.md)

## Category

enhancement

## What to build

A stage without a countdown is inert (Yara shipped with no clock, no plan). Give
every new campaign a spine: at least one antagonist/threat clock whose aim
completes off-screen, seeded at creation. Still one stage — but a live one.

- `/import` and `/new-game` seed ≥1 `threat-clocks.json` clock representing the
  antagonist's off-screen aim. Import grounds it in extracted plots; new-game
  authors it from tone/themes.
- Does NOT pre-build the world beyond this — one clock, not a gazetteer.

## Acceptance criteria

- [x] After `/import`, `threat-clocks.json` contains ≥1 seeded antagonist clock
      with a name, segments, and a consequence, grounded in the source. *(import.md
      now instructs `gm-clock.sh add "<aim>" 4 --on time --consequence "..."` after
      the stage)*
- [x] After `/new-game`, the same holds, authored from the world's tone/themes.
      *(new-game.md item 3b, same seed grounded in tone/themes)*
- [x] The seeded clock is a valid clock (advances via the existing
      `gm-clock.sh` machinery). *(uses `gm-clock.sh add`, the real tool; time-clocks
      tick on gm-time.sh)*
- [x] Seeding adds exactly the spine (no cascade of pre-built content). *("One
      clock, not a doom gazetteer")*

## Out of scope

- The graph edges (separate ticket) and any broader world pre-build.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-15T16:18:00Z — verified, fast-lane [ss-rt14b]
- import.md (after the stage) + new-game.md (item 3b) both instruct seeding ≥1 threat clock via `gm-clock.sh add "<aim>" 4 --on time --consequence "..."` whose aim completes off-screen — grounded in the book's plot / the world's tone. Framed "one clock, not a doom gazetteer" to preserve the anti-gazetteer rule.
- Uses the real `gm-clock.sh add` tool (validated usage); time-clocks tick on gm-time.sh. Prompt-only; fast-lane. Live proof is a creation play-through.

## History

- 2026-08-15T16:18:00Z  verified (prompt-only, fast-lane) → done + committed  [ss-rt14b]
- 2026-08-15T16:18:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:18:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
