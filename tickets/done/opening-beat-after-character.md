---
slug: opening-beat-after-character
title: Seed the opening beat once the PC exists, not before
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: gk-a8r14q
claimedAt: 2026-08-14T17:27:15Z
changedFiles: [lib/opening_seed.py, lib/player_manager.py, lib/identity_onboarding.py, .claude/commands/import.md, .claude/commands/new-game.md, tests/test_opening_seed.py, tests/test_new_game_parity.py, tests/test_identity_onboarding.py, docs/flows/import-a-book.md, docs/flows/author-a-world.md, docs/flows/onboarding-and-death.md]
resolution: opening re-seeds on first PC (onboard/unmatched set); --replace leaves a matched opening
reviewRounds: 3
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-14T18:30:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`gm-extract.sh seed-opening` runs during import (import.md Step 6) AND during
`/new-game` Phase E — both before the player has a character. It picks the
arc's first spine plot and writes the starting position, the opening beat,
and a session-log "Previously On" hook.

On the Conan import it seeded **The Scarlet Citadel** - a King-Conan beat that
opens with the PC already ruling Aquilonia and losing five thousand knights.
The player then chose to play the young pirate era, and every seeded artifact
was wrong: wrong location, wrong power level, wrong story. All three had to be
rewritten by hand. `/new-game` now has the same ordering bug.

The opening cannot be chosen before the protagonist is.

1. Either move `seed-opening` after character creation in both `/import` and
   `/new-game`, or make it re-seed when the active PC is first set
   (`gm-player.sh set`).
2. When the campaign has multiple viable entry arcs, the seeded opening should
   be selectable rather than forced to spine position 1.
3. Re-seeding must rewrite the starting location, the active plot, and the
   session-log hook together - a partial re-seed is what produced the
   inconsistent state here.

## Acceptance criteria

- [x] A fresh import OR /new-game followed by character creation produces an opening beat consistent with the created PC.
- [x] Re-seeding updates player position, active plot status, and the session-log hook atomically.
- [x] Only one plot is `active` after re-seeding (the previously seeded one is returned to available).
- [x] A test covers import → create character → opening beat matches.
- [x] (review) After a fresh import or `/new-game`, `gm-player.sh onboard` re-seeds location, the active plot, and the session-log hook to match that PC — without requiring a separate `gm-player.sh set`.
- [x] (review) If `current_character` is already set by onboard, a later `gm-player.sh set` still re-seeds when the opening has never been PC-matched (or onboard itself is the re-seed trigger).
- [x] (review) A PC named Conan whose concept/description is pirate-era selects Queen of the Black Coast (The Tigress), not The Scarlet Citadel.
- [x] (review) `onboard --replace` must not reseed when `overview.opening_matched_to_pc` is already true (same gate as `set_current_player`). First-PC `onboard` (flag unset) still reseeds.

## Out of scope

The spine ordering algorithm itself.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T18:30:00Z — pass [review-opening-2]
reviewed: perfect
Notes:
- player_manager.py docstring still says onboard always re-seeds (style)
- import-a-book.md leftover “onboard always re-seeds” (style)
- duplicate "into" in _STOP (style)

### 2026-08-14T18:06:58Z — fail [review-opening]
reviewed: needs-changes
- lib/player_manager.py:306 — Re-seed is wired only to set_current_player when current_character is empty. The default import / /new-game path is gm-player.sh onboard, which writes current_character itself (identity_onboarding.py:149) and never calls set.
- .claude/commands/import.md:696 / new-game.md:258 — claim first set re-seeds, but onboard already fills current_character so set never fires.
- lib/opening_seed.py:146 — Plot choice ranks NPC-name hits above concept/era; a PC named Conan with a pirate-era concept still picks The Scarlet Citadel.
- nits: sequential Path.replace not atomic; "into" duplicated in _STOP.

### 2026-08-14T18:06:58Z — verified [gk-a8r14q]
Criterion 1: import/new-game provisional seed + first `set_current_player` re-seeds to PC-matched plot — test_opening_seed + test_new_game_parity.
Criterion 2: reseed writes overview + plots + session-log via tmp+replace together.
Criterion 3: previously seeded spine plot returns to available; exactly one active.
Criterion 4: pirate-era Belit vs king-era spine covered in test_opening_seed.
Evidence: `uv run pytest tests/test_opening_seed.py tests/test_new_game_parity.py -q` — 14 passed.

## History

- 2026-08-14T18:30:00Z  reviewed perfect → done  [gk-a8r14q]
- 2026-08-14T18:06:58Z  review needs-changes (round 1) — onboard is the real first-PC path; Conan-name ranking; fix re-delegated  [gk-a8r14q]
- 2026-08-14T18:06:58Z  verified → in-review, review dispatched  [gk-a8r14q]
- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-14T17:27:15Z  claimed; scope widened to /new-game Phase E  [gk-a8r14q]
- 2026-08-14T17:56:17Z  doc-grounding confirmed — re-seed on first gm-player.sh set, both pipelines  [gk-a8r14q]
