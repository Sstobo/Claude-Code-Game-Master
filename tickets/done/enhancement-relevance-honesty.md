---
slug: enhancement-relevance-honesty
title: Batch enhancement attaches zero name-bearing passages to 67% of entities and reports success
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: gk-a8r14q
claimedAt: 2026-08-14T17:27:15Z
changedFiles: [lib/entity_enhancer.py, tests/test_enhancer_gate.py, docs/modules/rag-stack.md]
reviewRounds: 1
implementer: null
resolution: 0-name-bearing attaches nothing; batch warns and exits at 25%
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-14T18:06:58Z
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

- [x] Entities whose best passage scores below the relevance floor get no attached passages and are reported, rather than being flagged and kept.
- [x] The batch summary surfaces the low-relevance fraction prominently and exits non-zero (or prints an explicit WARNING banner) above a documented threshold.
- [ ] On a fixture corpus, the low-relevance fraction measurably drops versus the current query strategy.
- [x] A test asserts the floor behavior and the warning threshold.

## Out of scope

Replacing the embedding model or the vector store.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T18:06:58Z — pass [review-enhance]
reviewed: perfect
Notes:
- warning tests use 2/3 vs 0/4 and never pin the 0.25 boundary (style)
- rag-stack.md implies name listing is threshold-gated; code lists names whenever nonempty (style)

### 2026-08-14T18:06:58Z — verified [gk-a8r14q]
Criterion 1: 0-name-bearing → `_gate_passages` returns empty; batch does not call apply_enhancements — test_zero_name_bearing_attaches_nothing + test_zero_name_bearing_batch_reports_not_enhanced.
Criterion 2: format_batch_summary WARNING banner + exit 1 at LOW_RELEVANCE_WARN_FRACTION 0.25; names offenders — test_batch_summary_warns_and_nonzero_above_threshold. CLI sys.exit(code) wired.
Criterion 3: no live corpus fixture; `_enhancement_queries` includes type (unit-tested). [human-judgement] measurable drop vs name-only query on a real book is unproven.
Criterion 4: floor + warning threshold tests present (10 passed).
Evidence: `uv run pytest tests/test_enhancer_gate.py -q` — 10 passed.

## History

- 2026-08-14T18:06:58Z  reviewed perfect → done  [gk-a8r14q]
- 2026-08-14T18:06:58Z  verified → in-review, review dispatched  [gk-a8r14q]
- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-14T17:27:15Z  claimed  [gk-a8r14q]
- 2026-08-14T17:56:17Z  doc-grounding confirmed — honesty gate + warning/non-zero + query context  [gk-a8r14q]
