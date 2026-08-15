---
slug: lazy-npc-enrichment
title: Stub NPC gains an interior on first real interaction
category: enhancement
kind: hitl
priority: p2
lane: manual
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

enhancement

## What to build

Present NPCs correctly start as one-line stubs (don't pre-write). But the moment
the player meaningfully engages one, it should become a person — a want, a
secret, a line — and persist, so nobody the player actually talks to stays a
"neutral stub." This preserves the anti-gazetteer rule while fixing the flatness.

- Add guidance to the social flow (`gm-social` / CLAUDE.md): on first meaningful
  interaction with a stub NPC, author an interior (want / secret / voice line)
  and persist via existing `gm-npc.sh set-inner` / `update`.
- No new store; uses the fields NPCs already have.

## Acceptance criteria

- [ ] Social-flow guidance instructs the GM to enrich a stub on first meaningful
      interaction and persist it.
- [ ] Play-through: engaging a stub NPC results in a persisted interior
      (mood/goal/secret + a line) on that NPC's record.
- [ ] Uninvolved stubs are left thin (no pre-building).

## Out of scope

- Automatic/background enrichment of NPCs the player never engages.

## Verification

Lane: manual — verified by a human play-through confirming an engaged stub gains
and keeps an interior while untouched stubs stay thin.

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
