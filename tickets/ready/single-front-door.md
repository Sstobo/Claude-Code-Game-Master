---
slug: single-front-door
title: Collapse the entry maze into one front door (/dm canonical)
category: enhancement
kind: afk
priority: p2
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: []
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

The "IMPORT/SELECT YOUR ADVENTURE" menu is re-implemented in `setup.md`,
`import.md`, and `dm.md` STEP 0. Make `/dm` the single canonical entry; fold the
duplicated menu logic into one place the others reference. README, CLAUDE.md
first-run, and the welcome screen all point to `/dm`. A confused player at the
threshold should see exactly one obvious door.

## Acceptance criteria

- [ ] One canonical entry/menu definition; `setup.md`/`import.md`/`dm.md` reference it instead of re-implementing.
- [ ] `/dm` documented as THE entry point in README + CLAUDE.md first-run.
- [ ] No contradictory entry instructions remain across the command docs.
- [ ] Manual walkthrough: fresh-ish state lands the player at one clear next step.

## Verification

Lane: manual

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
