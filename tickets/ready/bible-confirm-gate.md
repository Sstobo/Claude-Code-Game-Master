---
slug: bible-confirm-gate
title: Draft-then-confirm review gate for the generated world/ruleset
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [import-longcontext-read]
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

Quality gate so auto-derived rules don't silently ship generic/wrong. After
import generates the world-bible + drafted ruleset + campaign_rules, present a
review step: show the human the drafted voice/factions/signature-systems +
proposed rules, allow edits, and require confirmation before the world becomes
playable. Middle path between fully-automatic and hand-authored.

## Acceptance criteria

- [ ] Import pauses at a review step presenting the drafted bible + ruleset + campaign_rules in human-readable form.
- [ ] The human can edit/approve/reject sections before play starts.
- [ ] An unconfirmed world is not marked playable.
- [ ] Confirmation persists the approved artifacts; rejection allows re-draft.
- [ ] Manual walkthrough on a sample import shows the gate working end-to-end.

## Verification

Lane: manual

## Blocked by

import-longcontext-read

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
