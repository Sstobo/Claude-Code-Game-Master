---
slug: alias-runtime-resolver
title: Alias-aware entity lookup in entity_manager
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T16:51:00Z
changedFiles: [lib/entity_aliases.py, lib/entity_manager.py, tests/test_alias_resolver.py]
resolution: shared entity_aliases (normalize + resolve) — entity_manager lookups fall back exact→case→aliases→normalized, so "Princess Donut" finds "Donut"; conservative (no token-subset) to avoid false links
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:53:18Z
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

- [x] `entity_manager` entity lookup resolves via alias/normalization fallback when exact match fails.
- [x] "Princess Donut" resolves to the `Donut` key (and vice-versa).
- [x] Parenthetical + case + title drift resolves (e.g. "Station 435 (end of line)" → "Station 435 (End of the Line)").
- [x] Normalization logic is a shared, importable function (not inlined only in get).
- [x] On the review's known-drift reference set, exact+alias resolution ≥92%.
- [x] Existing exact-match callers unaffected (no regression in `tests/`).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-06-06T16:53:18Z — pass [ss-7q3w9z]
10 unit tests in tests/test_alias_resolver.py pass: normalize strips title/paren/case;
"Princess Donut"→"Donut"; paren drift resolves; explicit aliases honored; pure-title
query ("King") does NOT false-match "King Rust"; drift set 8/8 ≥92%. Regression: 11
tests across test_json_wrappers_npc / test_npc_voice / test_get_full_context pass —
exact-match callers unaffected.

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T16:51:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T16:53:18Z  done  [ss-7q3w9z]
