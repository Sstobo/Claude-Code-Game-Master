---
slug: enhancement-relevance-honesty
title: Batch enhancement attaches zero name-bearing passages to 67% of entities and reports success
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

`gm-enhance.sh batch` on the Conan import finished with:

```
Enhanced: 675
Skipped:  0
Low-relevance (0 name-bearing, flagged): 454
Total:    675
```

454 of 675 entities - 67% - got passages that do not contain the entity's name
at all, and the run still reports as a clean success. Enhancement exists so the
GM can narrate NPCs in their own voices; two thirds of the cast got passages
about something else, silently.

1. Improve retrieval for the low-relevance case: entity name plus type/context
   in the query, and a relevance floor below which passages are not attached at
   all (an entity with no good passage is better than one with three wrong ones).
2. Make the summary honest: report the low-relevance fraction as a WARNING with
   a non-zero signal when it exceeds a threshold, not as a footnote under
   "Enhanced: 675".
3. Report the worst offenders by name so they can be inspected.

## Acceptance criteria

- [ ] Entities whose best passage scores below the relevance floor get no attached passages and are reported, rather than being flagged and kept.
- [ ] The batch summary surfaces the low-relevance fraction prominently and exits non-zero (or prints an explicit WARNING banner) above a documented threshold.
- [ ] On a fixture corpus, the low-relevance fraction measurably drops versus the current query strategy.
- [ ] A test asserts the floor behavior and the warning threshold.

## Out of scope

Replacing the embedding model or the vector store.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
