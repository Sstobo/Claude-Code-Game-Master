---
slug: opening-beat-seed
title: Seed the opening beat — start a fresh import at the book's opening
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [campaign-overview-author, plot-spine-extraction]
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T16:47:47Z
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

- [ ] Import sets `player_position` to the arc's opening location (from the spine).
- [ ] An opening cliffhanger/hook is written where session context reads it (overview/session-log seed).
- [ ] The first spine plot is marked `active` with an opening progress beat.
- [ ] A fresh `/dm` after import opens on the book's actual opening scene, not blank state.
- [ ] Verified on anarchists-cookbook: opens on the moving train above station 80 with the collapse clock live.

## Verification

Lane: agent

## Blocked by

campaign-overview-author, plot-spine-extraction

---

## QA Reports

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
