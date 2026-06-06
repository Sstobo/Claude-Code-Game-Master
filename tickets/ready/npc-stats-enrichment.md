---
slug: npc-stats-enrichment
title: Stats-enrichment pass for combat NPCs
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [cap-extraction-30]
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Combat/threat NPCs are not table-runnable: 0/65 have AC, 0/65 HP, CR on only 8/65.
Add a stats-enrichment pass (post-cap, post-extraction) that assigns HP/level and a
CR/difficulty proxy to combat-relevant NPCs (antagonists, bosses, monster-entities)
using the active World Kit via the monster-manual / rules-master agent. Explicitly
flag non-combatants as intentionally statless rather than leaving the field
ambiguously empty.

## Acceptance criteria

- [ ] Combat-relevant NPCs receive HP + a CR/difficulty proxy appropriate to the kit.
- [ ] Stats derived via the kit (not hardcoded 5e) — works for the DCC resource-axis kit.
- [ ] Non-combatant NPCs carry an explicit statless flag (distinguishable from "not yet enriched").
- [ ] Runs on the capped ≤30 NPC set.
- [ ] Verified: a known antagonist (e.g. Hekla) has runnable HP/CR after the pass.

## Verification

Lane: agent

## Blocked by

cap-extraction-30

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
