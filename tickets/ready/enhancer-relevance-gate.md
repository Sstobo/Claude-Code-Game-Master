---
slug: enhancer-relevance-gate
title: Relevance gate for RAG enhancement
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

`lib/entity_enhancer.py` attaches a fixed top-N of semantic neighbors regardless of
fit → 23/154 entities (14%) had ZERO passages naming them; rare entities over-padded
with the wrong scene, true canonical mention often omitted; ~155K tokens of noise.
Add a relevance gate: (1) force-include any chunk that literally contains the entity
name or a known alias as a seed passage; (2) fill remaining slots only with vector
neighbors above a similarity floor — DROP below-floor instead of padding to N;
(3) persist per-passage retrieval score + an entity-level name-match fraction;
(4) flag entities with zero name-bearing passages for re-enhance/curation.

## Acceptance criteria

- [ ] Enhancement force-includes ≥1 chunk literally naming the entity/alias when one exists in the corpus.
- [ ] Passages below the similarity floor are dropped, not used as padding.
- [ ] Each attached passage stores its retrieval score; each entity stores a name-match fraction.
- [ ] Entities with zero name-bearing passages are flagged (field or report).
- [ ] On a re-enhanced sample, name-bearing-passage coverage materially improves vs the 14%-zero baseline.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
