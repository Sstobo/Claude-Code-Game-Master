---
slug: recall-top-k
title: gm-recall.sh exposes --top-k; default raised to 5
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

`campaign_memory.py` recall and `gm-recall.sh` hard-cap what the GM can pull.
Expose `--top-k` (default raised to 5). Do **not** touch
`lib/session_manager.py`.

## Acceptance criteria

- [ ] `gm-recall.sh --top-k 8` returns 8 hits when at least 8 exist — test.
- [ ] Default (no flag) is 5 — test.
- [ ] Full suite passes; claiming memory docs restamped if they pin the old cap.

## Out of scope

THE WORLD REMEMBERS injection (already shipped); fence-disclosures;
session_manager.py.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-14T18:52:00Z  created → ready (split from advisory-fences)  [gk-t8n2wp]
