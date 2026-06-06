---
slug: rules-doc-authoring
title: Author substantive rules.md prose for the imported book/kit
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [campaign-overview-author]
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T16:47:47Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

ruleset.json is a thin router (stat schema / progression / resolution / agents) and
points `rules_doc` at a `rules.md` of actual rules PROSE — which doesn't exist for a
fresh import. `campaign-overview-author` only guarantees the pointer is valid
(null or stub). This ticket authors SUBSTANTIVE per-book rules prose: the kit's
signature systems explained for the DM (DCC: how viewers/leveling work, loot boxes,
the floor/stairwell structure, train mechanics, what beats the clock), grounded in
the source. `WorldKit.rules_doc_path()` loads it on demand; the prose is what gives
the otherwise-thin ruleset its real per-book value.

## Acceptance criteria

- [ ] A non-trivial `rules.md` is authored for the imported book, grounded in source material.
- [ ] ruleset.json `rules_doc` points at it and `WorldKit.rules_doc_path()` resolves.
- [ ] Content covers the kit's signature systems (for DCC: viewers/progression, loot boxes, floor/stairwell + train mechanics, clock).
- [ ] Prose is DM-facing rules guidance, not raw copied passages.
- [ ] Verified: a DCC import yields a rules.md a DM could run the floor from.

## Verification

Lane: agent

## Blocked by

campaign-overview-author

---

## QA Reports

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
