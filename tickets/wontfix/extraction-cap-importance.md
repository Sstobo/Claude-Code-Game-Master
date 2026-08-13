---
slug: extraction-cap-importance
title: Boost title/plot-named entities so marquee content survives the cap
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

`extraction_cap.py:73` scores importance as raw source mention-frequency. On a
story collection this drops the most famous content in the book.

Observed on the Conan import at cap 60: dropped **Tower of the Elephant** (the
title location of the best-known story), **the Scarlet Citadel**, and **Yara**
(its villain) - while keeping broad region names like Khitai that are simply
mentioned more often in passing.

1. Add a strong boost for entities whose name appears in a plot/story TITLE,
   and for entities referenced by a MAIN-type plot. A title match should
   outrank raw frequency.
2. Make `cap` idempotent and non-destructive: re-running with a different limit
   must not require re-running `normalize` from `extracted/` (which is archived
   later in the flow and may be gone). Either cap from a preserved full copy or
   record the dropped set so it can be restored.
3. Report drops as a restorable list, not just a truncated log line.

## Acceptance criteria

- [ ] With a fixture where a low-frequency entity is named in a MAIN plot title, that entity survives a cap that would drop it on frequency alone.
- [ ] `cap` run twice at different limits produces the correct result without an intervening `normalize`.
- [ ] Dropped entities are recoverable (restored from a preserved copy or a recorded drop file).
- [ ] Existing tests still pass.

## Out of scope

Changing the default cap limit, and the reconcile/stub passes.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]

## Triage note (2026-08-13, fable-sott1)

From plot-type-enum-unify: lib/extraction_cap.py:27 `_PLOT_TYPE_WEIGHT` ranks
threat and mystery at the unknown-type floor (weight 1), so imported threat
plots are the first the 30-cap drops. Include a weight fix (threat/mystery ≥
side) in this ticket's scope; import PLOT_TYPES from schemas rather than
adding a fifth local vocabulary.

## History addendum

- 2026-08-13T21:31:11Z  ready → wontfix: superseded by extraction-tiering (Trust the Agent review) — don't tune the cap's taste, stop the deletion; triage notes carried over  [fable-sott1]
