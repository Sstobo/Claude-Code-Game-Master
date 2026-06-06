---
slug: connection-key-normalize
title: Normalize location connection targets to real keys
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [alias-runtime-resolver]
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

bug

## What to build

~18 of ~65 location connection edges don't resolve: key-name mismatches ("Station
435 (end of line)" vs "…(End of the Line)", "Desperado Club (Station 131)" vs
"Desperado Club", three Trainyard spellings) and descriptive phrases stored as
targets ("Any line", "Transfer stations ending in 1", "Upper level via central
stairs"). Normalize every `connections.to` to an exact existing location key via the
shared alias normalizer; move pattern/rule statements out of `connections.to` into
`features`/`notes`. Reserve `connections.to` for real location keys only.

## Acceptance criteria

- [ ] All `connections.to` values are exact existing location keys after normalization.
- [ ] Rule/pattern phrases are relocated to features/notes, not left as connection targets.
- [ ] Connection-edge resolution rate ≈100% post-pass.
- [ ] Reuses the shared normalizer (no duplicate matching logic).

## Verification

Lane: agent

## Blocked by

alias-runtime-resolver

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
