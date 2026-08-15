---
slug: seed-bible-edges
title: Wire 2-4 faction/geography edges at creation
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: living-world
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:17:00Z
changedFiles: [.claude/commands/import.md, .claude/commands/new-game.md]
resolution: import/new-game prompts now wire 2-4 faction/geography edges at creation (example edges shipped, JSON validated) instead of empty graphs
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:17:00Z
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

- [x] After creation, the bible's faction and/or geography graphs contain 2–4
      edges connecting existing nodes with a named tension/relationship. *(import.md
      `--fields-json` example now ships edges; both prompts instruct "wire 2–4 edges")*
- [x] Edges reference only nodes that exist in the same graph. *(example edges use
      the same `id`s declared in `nodes`; faction edge shape `{from,to,relation}`,
      geography `{from,to,adjacency}` per schema — JSON validated)*
- [x] Import-seeded edges are grounded in the source; new-game edges fit the
      stated themes. *(guidance: "the villain's faction vs the player's, the caravan
      vs the hunt")*
- [x] Empty-graph worlds (no nodes) don't error — they simply seed no edges.
      *(guidance is additive; validate_bible accepts graphs with empty edges)*

## Out of scope

- A full relationship map / faction simulation — a few seed edges only.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-15T16:17:00Z — verified, fast-lane [ss-rt14b]
- import.md `--fields-json` example now ships 1 faction edge + 1 geography edge (was empty `edges:[]`), with the correct schema shapes (`{from,to,relation}` / `{from,to,adjacency}`) — JSON validated with `json.loads`. Both prompts add "wire 2–4 edges (tension/adjacency), nodes without edges are a cast list."
- Prompt-only guidance change; fast-lane (no code logic). Live proof is a creation play-through.

## History

- 2026-08-15T16:17:00Z  verified (prompt-only, fast-lane) → done + committed  [ss-rt14b]
- 2026-08-15T16:17:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:17:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
