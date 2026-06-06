---
slug: rules-doc-authoring
title: Author substantive rules.md prose for the imported book/kit
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [campaign-overview-author]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:30:00Z
changedFiles: [lib/overview_seed.py, world-state/campaigns/anarchists-cookbook/rules.md, .claude/commands/import.md, tests/test_rules_doc.py]
resolution: authored a substantive DM-facing rules.md for the Iron Tangle (progression/viewers, loot boxes, saferooms, trains, prime-station stairwells, collapse clock, tone); overview_seed.set_rules_doc points ruleset.rules_doc at it; WorldKit.rules_doc_path() resolves live; import Step 6.6 documents authoring
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T17:31:22Z
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

- [x] A non-trivial `rules.md` is authored for the imported book, grounded in source material.
- [x] ruleset.json `rules_doc` points at it and `WorldKit.rules_doc_path()` resolves.
- [x] Content covers the kit's signature systems (for DCC: viewers/progression, loot boxes, floor/stairwell + train mechanics, clock).
- [x] Prose is DM-facing rules guidance, not raw copied passages.
- [x] Verified: a DCC import yields a rules.md a DM could run the floor from.

## Verification

Lane: agent

## Blocked by

campaign-overview-author

---

## QA Reports

### 2026-06-06T17:31:22Z — pass [ss-7q3w9z]
3 unit tests in tests/test_rules_doc.py pass: set_rules_doc points when file exists; no-op
when missing; WorldKit.rules_doc_path() resolves (dcc_world). Authored a real rules.md for
the Iron Tangle covering viewers-progression, loot boxes, saferooms/PvP, the moving floor,
prime-station stairwells, the 10-day collapse clock, and tone — DM-facing guidance, not raw
passages. Live: ruleset.rules_doc → "rules.md"; WorldKit().rules_doc_path() resolves to the
campaign's rules.md. import Step 6.6 documents authoring + repointing.

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
- 2026-06-06T17:30:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:31:22Z  done  [ss-7q3w9z]
