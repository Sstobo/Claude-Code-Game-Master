---
slug: party-promote-real-stats
title: gm-npc.sh promote must carry the NPC's real stats, not default HP 10 / AC 10
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
reviewRounds: null
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T16:20:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`bash tools/gm-npc.sh promote "Belit"` reported:

```
[SUCCESS] Belit is now a party member (HP: 10/10, AC: 10)
```

Bêlit is a pirate queen who commands a corsair fleet, and the import's
`stat-npcs` pass had already assigned her a difficulty proxy (hp 120, cr 8,
difficulty boss). `promote` ignored it and applied a flat default, so a
principal ally joined the party as the weakest thing on the board. Her stats
had to be hand-patched after the fact.

Any promoted NPC with existing `stats` (from `stat-npcs` or a monster-manual
lookup) must carry them into party membership; only a genuinely statless NPC
should receive defaults, and that should be reported as such.

## Acceptance criteria

- [ ] Promoting an NPC that has `stats` produces party HP/AC derived from those stats, not 10/10.
- [ ] Promoting a statless NPC applies defaults and says so explicitly in the output.
- [ ] The promote output prints the source of the stats it used.
- [ ] A test asserts both paths.

## Out of scope

The accuracy of `stat-npcs` difficulty proxies themselves.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
