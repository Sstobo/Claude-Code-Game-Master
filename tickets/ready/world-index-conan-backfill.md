---
slug: world-index-conan-backfill
title: Regenerate the conan campaign's index
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: world-index
blockedBy: [world-index-import-swarm]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
---

## Parent

World Index (prds/world-index.md)

## Category

enhancement

## What to build

Fix the real campaign that surfaced the bug: regenerate the conan
`world-bible.json` through the new import index pass so its junk `chapters` are
gone and a real roster exists. Validates the import path on the actual corpus.

## Acceptance criteria

- [ ] `world-state/campaigns/conan/world-bible.json` has a populated `index`
      (npcs / locations / items / monsters).
- [ ] The `chapters` array is gone.
- [ ] Entries are well-formed one-sentence notes for **named** entities; no
      mid-sentence fragments, page markers, or copyright lines.
- [ ] Recognizable Conan roster is present (e.g. Yara, the Tower of the Elephant,
      the Heart of the Elephant, Yag-kosha).
- [ ] The index rides into `gm-session.sh context` for the conan campaign.

## Out of scope

- Migrating other campaigns (conan is the only real one today).

## Verification

Lane: agent

## Blocked by

world-index-import-swarm

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
