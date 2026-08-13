---
slug: guard-consolidation
title: One campaign-guard implementation; unified message; unknown-action ordering
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T18:45:00Z
updatedAt: 2026-08-13T18:45:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

enhancement

## What to build

Post-wave-1 cleanup from review-startup (all non-blocking notes):

1. Three identical wrapper-local `require_campaign()` copies live in
   gm-session.sh, gm-enhance.sh, gm-worldgen.sh (written while common.sh was
   owned by another ticket, now landed). Consolidate into common.sh —
   either upgrade `require_active_campaign`'s message (it still says "Run
   /new-game or /import first", which CLAUDE.md's decision tree now calls
   wrong for the campaigns-exist state) or have it print the list/switch
   guidance; delete the three copies. `grep -c require_campaign tools/*.sh`
   ends at 0.
2. Guard ordering: gm-session.sh fires the guard before the `*)` unknown-
   action branch, so a typo'd verb reports "No active campaign" instead of
   "Unknown action"; `--help` also hits the guard. Route help/unknown-action
   before the guard (match gm-enhance.sh's help exemption).
3. gm-worldgen.sh `""|--*` name detection is order-sensitive
   (`consolidate --json my-world` guards despite a name) — parse the name
   positionally regardless of flag order or document flag-last.
4. Pin the bootstrap escape hatch: a test asserting
   `gm-worldgen.sh consolidate <campaign>` reaches world_author with
   active-campaign.txt absent.

## Acceptance criteria

- [ ] One guard implementation repo-wide, message includes the list/switch guidance.
- [ ] `gm-session.sh --help` and `gm-session.sh typo` (no campaign) print usage / unknown-action respectively.
- [ ] Explicit-name worldgen verbs run pre-activation regardless of flag order (test-pinned).
- [ ] Full suite passes.

## Out of scope

New guard coverage for other tools; --json envelope work.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T18:45:00Z  created → ready (from review-startup notes)  [fable-sott1]
