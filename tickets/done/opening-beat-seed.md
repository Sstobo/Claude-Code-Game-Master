---
slug: opening-beat-seed
title: Seed the opening beat — start a fresh import at the book's opening
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [campaign-overview-author, plot-spine-extraction]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:18:00Z
changedFiles: [lib/opening_seed.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_opening_seed.py]
resolution: dm-extract.sh seed-opening sets player_position to the arc's opening location, marks the first spine plot active with an opening beat, and writes a session-log Previously-On/cliffhanger block; live context now opens on the Iron Tangle moving train with the collapse clock live
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T17:20:45Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

A fresh import drops the player into a blank state with no entry point. Seed the
campaign's opening from the book: set starting `player_position.current_location`
to the arc's opening location, write an opening cliffhanger / "scene zero" hook, and
mark the first spine plot `active` with its opening beat populated (via plot_manager
update). After character creation, the first `/dm` session should begin AT the book's
actual opening, not a void.

## Acceptance criteria

- [x] Import sets `player_position` to the arc's opening location (from the spine).
- [x] An opening cliffhanger/hook is written where session context reads it (overview/session-log seed).
- [x] The first spine plot is marked `active` with an opening progress beat.
- [x] A fresh `/dm` after import opens on the book's actual opening scene, not blank state.
- [x] Verified on anarchists-cookbook: opens on the moving train above station 80 with the collapse clock live.

## Verification

Lane: agent

## Blocked by

campaign-overview-author, plot-spine-extraction

---

## QA Reports

### 2026-06-06T17:20:45Z — pass [ss-7q3w9z]
4 unit tests in tests/test_opening_seed.py pass: sets position + marks beat + writes log;
opening beat idempotent on re-run; no-spine returns not-seeded; fresh get_full_context opens
on the book opening ("moving train above station 80" + [main] thread, dcc_world). Live apply
on anarchists-cookbook: player_position → The Iron Tangle; first spine plot active with opening
beat; dm-session.sh context shows PREVIOUSLY ON + WHERE WE PAUSED + arc-ordered STORY THREADS
+ the 10-day collapse clock.
[note] The existing session-summary parser folds footer lines into the summary text (pre-existing
behavior, same for real end_session blocks) — cosmetic, not introduced here.

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
- 2026-06-06T17:18:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:20:45Z  done  [ss-7q3w9z]
