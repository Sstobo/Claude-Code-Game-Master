---
slug: cap-extraction-30
title: Cap extraction to top-30 per type, importance-ranked
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Cap each extracted type (npcs, locations, items, plots) at 30 entities, keeping the
30 MOST PLAYABLE. Selection = importance ranking, not naive first-30 or raw agent
dump. Ranking signal: source mention-frequency + main-cast / load-bearing priority
(protagonist party, recurring antagonists, hub locations, signature items, main
plotlines). Apply as a post-extraction filter (deterministic, in
`lib/agent_extractor.py` / a normalize step) so it is independent of agent judgment.
Log how many of each type were dropped.

## Acceptance criteria

- [ ] Each of npcs/locations/items/plots written to campaign root has ≤30 entries.
- [ ] Kept set chosen by importance score (mention-frequency + main-cast/load-bearing weight), not file order.
- [ ] Main cast / protagonist party never dropped (e.g. for a DCC import: Carl, Donut, Mordecai, Katia, Mongo present if extracted).
- [ ] Dropped count per type is logged/reported to the user during import.
- [ ] Cap is configurable (constant or flag), defaulting to 30.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
