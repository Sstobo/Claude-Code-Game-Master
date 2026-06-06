---
slug: campaign-overview-author
title: Author campaign-overview + campaign_rules; fix rules_doc pointer
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

Import copies/creates ruleset.json (Step 6.5) but leaves campaign-overview.json as
the default scaffold (genre "Fantasy", date "Year 1", no campaign_rules) → signature
book systems live nowhere the DM tooling reads. Also ruleset.json copied from a
sibling kit can carry a dangling `rules_doc: "rules.md"` with no file on disk.
Add a mandatory post-kit authoring step to import: write a real campaign-overview
(campaign_name, genre, tone weights, in-world date) AND a `campaign_rules` block
capturing the book's signature systems (for DCC: loot boxes, viewers economy, train
mechanics, prime-station stairwells). Resolve `rules_doc`: write the file or set null.

## Acceptance criteria

- [ ] After import, campaign-overview.json has a book-appropriate name/genre/tone/date (not the default scaffold).
- [ ] campaign-overview.json contains a non-empty `campaign_rules` block surfaced by `world_kit.campaign_rules()` / scene context.
- [ ] ruleset.json `rules_doc` either points at an existing file or is null (no dangling pointer).
- [ ] import.md documents this as a required step (follow-on to Step 6.5).
- [ ] Verified on a fresh import: overview + campaign_rules + valid rules_doc all present.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
