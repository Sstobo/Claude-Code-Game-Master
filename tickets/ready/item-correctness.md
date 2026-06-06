---
slug: item-correctness
title: Item correctness — cursed flag, type taxonomy, value field
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

bug

## What to build

Item extraction slips: (1) Scavenger Mother crossbow mis-flagged `cursed:true` from
lore keyword-matching — it's a clean-upside legendary, and DCC boxes don't yield
cursed items. (2) `wondrous` type overloaded across keys/portals/lootboxes/coupons.
(3) `value` empty on 33/37 and the one populated entry holds box-contents, not worth.
Tighten the extractor's cursed heuristic to require an actual mechanical
penalty/binding clause on the item itself; introduce DCC-appropriate item types
(key, portal, lootbox, coupon) so loot-dropper can filter; null/drop `value` for the
DCC kit and move box-contents text into description/mechanics.

## Acceptance criteria

- [ ] `cursed:true` requires a real mechanical penalty/binding clause; Scavenger Mother crossbow → `cursed:false`.
- [ ] Item type taxonomy includes key/portal/lootbox/coupon; previously-"wondrous" misfits reclassified.
- [ ] `value` is null/omitted for the DCC kit; box-contents text lives in description/mechanics, not value.
- [ ] Changes are in the extractor heuristics / schema (repeatable on future imports), not just hand-edits.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
