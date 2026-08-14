---
slug: clock-tick-magnitude
title: Time advances clocks by elapsed magnitude, not one tick per call
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: trust-the-agent
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-14T18:52:00Z
updatedAt: 2026-08-14T18:52:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md) · split from advisory-fences

## Category

enhancement

## What to build

`gm-time.sh` and `threat_clocks.py` advance time-clocks by one tick per call,
so three weeks and ten minutes are the same pressure. Accept elapsed
magnitude (`--ticks N`, or derived from a duration argument) so a long
advance moves clocks proportionally.

Do **not** touch `lib/session_manager.py` — other tickets own that file.

## Acceptance criteria

- [ ] A multi-day `gm-time.sh` advance ticks time-clocks proportionally (not +1) — test.
- [ ] A minutes-scale advance still ticks +1 (or the documented minimum) — test.
- [ ] Full suite passes; living-world.md restamped where the claim moves.

## Out of scope

Consequence tick disclosures (fence-disclosures); relative-time verb itself;
session_manager.py.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-14T18:52:00Z  created → ready (split from advisory-fences)  [gk-t8n2wp]
