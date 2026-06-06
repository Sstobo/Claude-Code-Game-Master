---
slug: alias-runtime-resolver
title: Alias-aware entity lookup in entity_manager
category: bug
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

bug

## What to build

Runtime lookup is exact-match only (`lib/entity_manager.py:137` `entities.get(name)`),
so naming drift = broken links (plot→loc resolution only 19% exact). Add an
alias-aware resolver: before failing an exact `.get()`, normalize the query and keys
by (a) stripping leading titles ("Princess", "King", "Prince", "Mistress", etc.),
(b) stripping parentheticals, (c) case-folding, (d) trimming whitespace. Also honor
an explicit `aliases` list on an entity if present. Expose the normalization as a
shared util (reused by integrity-gate + connection-normalize tickets).

## Acceptance criteria

- [ ] `entity_manager` entity lookup resolves via alias/normalization fallback when exact match fails.
- [ ] "Princess Donut" resolves to the `Donut` key (and vice-versa).
- [ ] Parenthetical + case + title drift resolves (e.g. "Station 435 (end of line)" → "Station 435 (End of the Line)").
- [ ] Normalization logic is a shared, importable function (not inlined only in get).
- [ ] On the review's known-drift reference set, exact+alias resolution ≥92%.
- [ ] Existing exact-match callers unaffected (no regression in `tests/`).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
