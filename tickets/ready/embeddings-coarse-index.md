---
slug: embeddings-coarse-index
title: Demote embeddings to a coarse chapter index; pluggable embedder
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [import-longcontext-read]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Stop routing fidelity through weak MiniLM 3000-char chunks. Demote embeddings to
a COARSE chapter index whose job is only to point INTO the retained text (which
long-context reading then consumes). Make the embedder pluggable and branch query
templates by content type (literary vs game-module) so importing a novel stops
dragging retrieval toward D&D stat-block vocabulary.

## Acceptance criteria

- [ ] Embedding store indexes at chapter/section granularity pointing into the kept text, not fidelity-bearing 3000-char chunks.
- [ ] Embedder is pluggable via config (swap model without code changes).
- [ ] Query templates branch by content type (literary vs game-module).
- [ ] Retrieval returns chapter pointers that the long-context reader can load.
- [ ] Test: index a sample text → query → returns the right chapter pointer.

## Verification

Lane: agent

## Blocked by

import-longcontext-read

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
