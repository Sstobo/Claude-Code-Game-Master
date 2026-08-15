---
slug: entity-dedupe-materialize
title: Dedupe NPC identity on the materialize path (no second Aratus)
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: living-world
blockedBy: []
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

Living World (prds/living-world.md)

## Category

bug

## What to build

`npcs.json` held Aratus twice — once as a long play-pack-named stub ("Aratus the
Kothian (a fat, boastful kidnapper up from Koth)") and once as the real
materialized record ("Aratus"). The `alias-dedupe-integrity` guard (done) isn't
covering the play-pack → materialize path.

- Extend the existing dedup/alias guard so that materializing an NPC that already
  exists as a present-cast stub resolves to ONE record (merge onto the canonical
  name), rather than creating a second.
- Reproduce with the conan play-pack cast first, then fix.

## Acceptance criteria

- [ ] Reproduction: materializing a play-pack stub NPC currently yields two
      records; documented in the QA report.
- [ ] After the fix, the stub and the fleshed record resolve to a single NPC
      entry keyed on the canonical name.
- [ ] Existing `alias-dedupe-integrity` behavior for other paths is preserved
      (no regression).
- [ ] The conan `npcs.json` duplicate is not reintroduced by a re-materialize.

## Out of scope

- Cleaning the already-dead Aratus data in conan by hand (the fix should make
  re-runs correct; a one-off data cleanup can ride with conan-backfill if needed).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
