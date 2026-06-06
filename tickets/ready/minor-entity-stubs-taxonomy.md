---
slug: minor-entity-stubs-taxonomy
title: Stub referenced minor entities; fix plot taxonomy
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [import-integrity-gate]
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

bug

## What to build

A few referenced antagonists have no backing entity (Ji-Hoon assassin, Blister/Wrath
Ghouls, ram-headed Club Vanquisher cleric, Rusalka Station 84); one plot uses
off-taxonomy `type: optional`. For named threats referenced by plots/NPCs but absent
from npcs.json: create minimal monster/NPC stubs (or convert to generic monster
references the monster-manual agent can stat on demand). Fix plot taxonomy: reclassify
"Build the Royal Court" from `optional` to `side` (or add `optional` to the documented
enum) so all plot types are valid.

## Acceptance criteria

- [ ] Named threats referenced but missing get a minimal stub or a generic monster reference.
- [ ] No plot uses an off-enum `type`; either reclassified or the enum is extended + documented.
- [ ] Runs within / after the integrity gate so new stubs satisfy reference resolution.
- [ ] Overlap with enhancer relevance gate noted, not duplicated.

## Verification

Lane: agent

## Blocked by

import-integrity-gate

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
