---
slug: item-correctness
title: Item correctness — cursed flag, type taxonomy, value field
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:24:00Z
changedFiles: [lib/item_fixup.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_item_fixup.py]
resolution: dm-extract.sh fix-items clears cursed unless MECHANICS state a real penalty (lore curses cleared), reclassifies wondrous→key/portal/lootbox/coupon, nulls non-price value (text→mechanics); live cleared the Scavenger crossbow + retyped 18 items
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:25:14Z
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

- [x] `cursed:true` requires a real mechanical penalty/binding clause; Scavenger Mother crossbow → `cursed:false`.
- [x] Item type taxonomy includes key/portal/lootbox/coupon; previously-"wondrous" misfits reclassified.
- [x] `value` is null/omitted for the DCC kit; box-contents text lives in description/mechanics, not value.
- [x] Changes are in the extractor heuristics / schema (repeatable on future imports), not just hand-edits.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-06-06T17:25:14Z — pass [ss-7q3w9z]
7 unit tests in tests/test_item_fixup.py pass: lore curse w/o mechanical penalty cleared;
real penalty keeps cursed; wondrous→key/portal/lootbox/coupon by keyword; known types
untouched; non-price value moved to mechanics + nulled; real price kept; run writes. Live
apply on anarchists-cookbook: Scavenger Mother crossbow cursed→False, 18 wondrous items
retyped, 1 non-price value cleared. Deterministic pass (dm-extract.sh fix-items), repeatable.

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:24:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:25:14Z  done  [ss-7q3w9z]
