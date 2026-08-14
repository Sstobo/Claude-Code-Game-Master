---
slug: recall-top-k
title: gm-recall.sh exposes --top-k; default raised to 5
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: trust-the-agent
blockedBy: []
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T18:54:05Z
changedFiles: [lib/campaign_memory.py, tools/gm-recall.sh, tests/test_campaign_memory.py, docs/modules/campaign-memory.md]
reviewRounds: 2
resolution: recall default top-k is 5; gm-recall.sh --top-k is tested through the wrapper
updatedAt: 2026-08-14T19:26:00Z
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

- [x] `gm-recall.sh --top-k 8` returns 8 hits when at least 8 exist — test.
- [x] Default (no flag) is 5 — test.
- [x] Full suite passes; claiming memory docs restamped if they pin the old cap.
- [x] (review) `bash tools/gm-recall.sh recall <unique-token> --top-k 8` (the wrapper) returns exactly 8 hits when the active campaign has ≥8 matching entries.
- [x] (review) `bash tools/gm-recall.sh recall <unique-token>` with no `--top-k` returns exactly 5 hits when ≥5 matching entries exist.

## Out of scope

THE WORLD REMEMBERS injection (already shipped); fence-disclosures;
session_manager.py.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T19:26:00Z — pass [9b53f9ba]
reviewed: perfect (followup). Wrapper tests: no --top-k → 5; --top-k 8 → 8.
Notes:
- Default 5 is duplicated on recall() and argparse; both paths tested.

### 2026-08-14T19:16:00Z — fail [70d555eb]
reviewed: needs-changes
- tests/test_campaign_memory.py:113 — `--top-k 8` is asserted by subprocessing `lib/campaign_memory.py`, not `bash tools/gm-recall.sh`.
- tests/test_campaign_memory.py:103 — default 5 is tested only as `CampaignMemory.recall()`; CLI argparse default untested.

### 2026-08-14T19:06:00Z — verified [gk-t8n2wp]
recall default top_k=5; CLI --top-k wired; 11 memory tests + full suite pass.

## History

- 2026-08-14T19:26:00Z  done: recall default top-k is 5; gm-recall.sh --top-k is tested through the wrapper  [gk-t8n2wp]
- 2026-08-14T19:18:00Z  followup review dispatched — wrapper CLI tests  [gk-t8n2wp]
- 2026-08-14T19:16:00Z  review needs-changes — wrapper CLI tests; fix delegated  [gk-t8n2wp]
- 2026-08-14T19:06:00Z  verified → in-review, review dispatched  [gk-t8n2wp]

- 2026-08-14T18:55:00Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:54:05Z  claimed  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  created → ready (split from advisory-fences)  [gk-t8n2wp]
