---
slug: clock-tick-magnitude
title: Time advances clocks by elapsed magnitude, not one tick per call
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: trust-the-agent
blockedBy: []
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T18:54:05Z
changedFiles: [tools/gm-time.sh, lib/time_manager.py, lib/threat_clocks.py, tests/test_threat_clocks.py, docs/modules/living-world.md]
reviewRounds: 1
resolution: time-clocks scale with --ticks/--duration; default remains +1
updatedAt: 2026-08-14T19:16:00Z
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

- [x] A multi-day `gm-time.sh` advance ticks time-clocks proportionally (not +1) — test.
- [x] A minutes-scale advance still ticks +1 (or the documented minimum) — test.
- [x] Full suite passes; living-world.md restamped where the claim moves.

## Out of scope

Consequence tick disclosures (fence-disclosures); relative-time verb itself;
session_manager.py.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T19:16:00Z — pass [066b6296]
reviewed: perfect
Notes:
- tests/test_threat_clocks.py:15 — `_active` is defined twice (harmless redefinition)
- living-world.md now lists `/lib/time_manager.py` as a source (ingest close-out for the duration map)

### 2026-08-14T19:06:00Z — verified [gk-t8n2wp]
--ticks N and --duration (days→N, weeks→7N, minutes/hours→1); default +1. 14 clock tests + full suite pass.

## History

- 2026-08-14T19:16:00Z  done: time-clocks scale with --ticks/--duration; default remains +1  [gk-t8n2wp]
- 2026-08-14T19:06:00Z  verified → in-review, review dispatched  [gk-t8n2wp]

- 2026-08-14T18:55:00Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:54:05Z  claimed  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  created → ready (split from advisory-fences)  [gk-t8n2wp]
