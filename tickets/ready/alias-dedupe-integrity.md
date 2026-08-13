---
slug: alias-dedupe-integrity
title: Resolve diacritic/parenthetical aliases; stop duplicate stubs; integrity must catch near-dupes
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
reviewRounds: null
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T16:20:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`stub-npcs` created a second Bêlit alongside the already-extracted `Belit`,
keyed by a 95-character descriptive string:
`"Bêlit (Shemite pirate queen of the Black Coast, mistress of the Tigress,
worshipped as a goddess by her crew)"`. The alias resolver missed it across two
axes at once - a diacritic (ê vs e) AND a parenthetical qualifier.

The integrity gate then reported **0 unresolved / 0 aliased** - a clean bill of
health over a duplicated principal character. The GM would treat them as two
people: one with rich extracted prose, one an auto-stub with boss stats.

Related: `reconcile` dropped 109 location references including "The Scarlet
Citadel and the pits beneath it" - a real place in the book - while stubbing
156 others. Its resolve/stub/drop decision needs the same alias handling.

1. Normalize for matching: strip diacritics, lowercase, strip trailing
   parenthetical qualifiers, collapse whitespace - before deciding a reference
   is unresolved.
2. Never create a stub whose normalized key matches an existing entity; record
   the descriptive string as an `alias` on the existing record instead.
3. The integrity gate must detect and report near-duplicate keys rather than
   passing silently.

## Acceptance criteria

- [ ] A fixture with `Belit` present and a reference to `Bêlit (long qualifier)` produces zero new stubs and one alias recorded on the existing record.
- [ ] `integrity` reports near-duplicate keys as findings instead of reporting 0 unresolved.
- [ ] `reconcile` resolves descriptive location phrasings to existing nodes via the same normalizer before dropping them.
- [ ] A test asserts the diacritic + parenthetical case for both NPCs and locations.

## Out of scope

Merging entity records that are genuinely distinct, and the cap ranking
(extraction-cap-importance).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
