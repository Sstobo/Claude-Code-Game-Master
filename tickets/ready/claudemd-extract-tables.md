---
slug: claudemd-extract-tables
title: Extract 5e/lookup tables out of CLAUDE.md into on-demand Skills
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [world-kit-schema]
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

First, safe step of the CLAUDE.md split (incremental per red-team). Move the pure
LOOKUP TABLES and mechanics blocks (XP-by-CR, spell slots, hit dice, conditions,
level-up ceremony, dungeon modes) out of the always-on 1196-line CLAUDE.md into
on-demand Skills that load only when triggered. Do NOT move the core loop,
persist-before-narrate, the action router, or the craft wisdom yet (that's the
next ticket). Verify each extracted skill loads reliably before extracting the
next.

## Acceptance criteria

- [ ] Lookup-table/mechanics blocks moved into discrete Skills (combat, spellcasting, conditions, level-up, dungeon).
- [ ] CLAUDE.md references the skills instead of inlining the tables.
- [ ] Core loop + persist-before-narrate + action router REMAIN in always-on CLAUDE.md.
- [ ] Each extracted skill verified to load on its trigger (manual or scripted check) before the next is extracted.
- [ ] No behavior regression on a representative combat + skill-check + level-up flow (manual smoke acceptable).

## Verification

Lane: agent

## Blocked by

world-kit-schema

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
