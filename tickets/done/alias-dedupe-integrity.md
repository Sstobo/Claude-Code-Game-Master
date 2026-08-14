---
slug: alias-dedupe-integrity
title: Resolve diacritic/parenthetical aliases; stop duplicate stubs; integrity must catch near-dupes
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: gk-a8r14q
claimedAt: 2026-08-14T17:27:15Z
changedFiles: [lib/entity_aliases.py, lib/integrity_gate.py, lib/minor_stubs.py, lib/location_reconcile.py, tests/test_alias_resolver.py, tests/test_integrity_gate.py, tests/test_location_reconcile.py, tests/test_minor_stubs.py, docs/modules/entity-graph.md]
resolution: fold diacritics; refuse near-dupe stubs; integrity reports duplicate keys
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-14T18:06:58Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Parentheticals and titles already fold in `normalize_entity_name`. The remaining
hole is diacritics: `\w` keeps `ê`, so `Bêlit` never matches `Belit`. Conan
`stub-npcs` created a second Bêlit keyed by a 95-character descriptive string
next to extracted `Belit`. Integrity reported 0 unresolved / 0 aliased over the
duplicate. `reconcile` still drops descriptive location phrasings that would
match after the same fold.

1. Fold diacritics in `normalize_entity_name` (NFKD + strip combining marks)
   before deciding a reference is unresolved. Do not re-implement parenthetical
   / title stripping — it already works.
2. Never create a stub whose normalized key matches an existing entity; record
   the descriptive string as an `alias` on the existing record instead.
3. The integrity gate must detect and report near-duplicate keys (normalized
   equality across existing entity keys) rather than passing silently.

## Acceptance criteria

- [x] A fixture with `Belit` present and a reference to `Bêlit (long qualifier)` produces zero new stubs and one alias recorded on the existing record.
- [x] `integrity` reports near-duplicate keys as findings instead of reporting 0 unresolved.
- [x] `reconcile` resolves descriptive location phrasings to existing nodes via the same normalizer before dropping them.
- [x] A test asserts the diacritic + parenthetical case for both NPCs and locations.

## Out of scope

Merging entity records that are genuinely distinct, and the cap ranking
(extraction-cap-importance).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T18:06:58Z — pass [review-alias]
reviewed: perfect
Notes:
- lib/entity_aliases.py:13 — module doc overstates who calls reuse_existing_key (style)
- lib/integrity_gate.py:149 — --no-strict help omits near-duplicates (style)
- _add_alias duplicated in minor_stubs and location_reconcile (style)

### 2026-08-14T18:06:58Z — verified [gk-a8r14q]
Criterion 1: Belit + `Bêlit (long qualifier)` → zero stubs, alias on Belit — test_minor_stubs + test_alias_resolver.
Criterion 2: integrity reports near-duplicate keys; strict mode fails — test_integrity_gate.
Criterion 3: reconcile reuses existing location for descriptive phrasing — test_location_reconcile.
Criterion 4: diacritic + parenthetical covered for NPCs and locations.
Evidence: `uv run pytest tests/test_alias_resolver.py tests/test_integrity_gate.py tests/test_location_reconcile.py tests/test_minor_stubs.py -q` — 39 passed (full four-ticket run 65 passed).

## History

- 2026-08-14T18:06:58Z  reviewed perfect → done  [gk-a8r14q]
- 2026-08-14T18:06:58Z  verified → in-review, review dispatched  [gk-a8r14q]
- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-14T17:27:15Z  claimed; scoped to diacritics + near-dupes (parentheticals already land)  [gk-a8r14q]
- 2026-08-14T17:56:17Z  doc-grounding confirmed — diacritic fold + near-dupe integrity + stub/reconcile aliasing  [gk-a8r14q]
