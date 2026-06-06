---
slug: loremaster-per-scene
title: Per-scene Loremaster (cached long-context grounding) + book-grounded agents
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [import-longcontext-read, embeddings-coarse-index]
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

Deepest fidelity, deliberately LAST (cost/latency risk per red-team). A
Loremaster subagent owns retrieval but uses the coarse index only to FIND
relevant chapters, then reads large spans into context and returns a synthesized,
grounded scene/NPC brief in the author's voice — instead of stapling nearest-
neighbor chunks. Cache briefs per location; deep-dive ONLY on new/important
scenes, never reflexively on routine turns. Rewrite monster-manual + rules-master
to (1) query the imported book first, (2) fall back to model knowledge of that
fictional world, (3) keep the dnd5eapi path only when the active kit is D&D — so
a sandworm or Balrog gets statted in the active system's terms.

## Acceptance criteria

- [ ] Loremaster finds relevant chapters via the coarse index, then reads spans and returns a voice-grounded brief.
- [ ] Briefs cached per location; deep reads gated to new/important scenes (NOT every turn).
- [ ] monster-manual + rules-master query the imported book first, fall back to model knowledge, use dnd5eapi only for a D&D kit.
- [ ] A non-D&D creature (e.g. sandworm) gets statted in the active kit's terms, grounded in source passages.
- [ ] Per-scene token/latency cost is logged; routine turns do not trigger a deep read.
- [ ] Test: cached brief is reused on revisit; a fresh important scene triggers one deep read.

## Verification

Lane: agent

## Blocked by

import-longcontext-read, embeddings-coarse-index

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
