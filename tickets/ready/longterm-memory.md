---
slug: longterm-memory
title: Long-term campaign memory — memory RAG + tiered memoir + dm-recall
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [story-spine-context, embeddings-coarse-index]
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

Make a 50-session campaign remember itself. Embed the campaign's OWN lived
history (session logs, facts, NPC timelines, resolved threads) into a dedicated
`campaign-memory` RAG collection refreshed on every save, with a `dm-recall` that
semantically surfaces "have we been here / met them / promised this before?" on
scene entry. Maintain a tiered consolidating memoir (always-on arc summary,
recent verbatim, older compressed, archive retrievable) so memory stays
high-signal and bounded. Add a provenance/importance dimension separating
book-canon from our-story so a huge imported world stays out of always-loaded
context while the NPCs you actually tangled with surface. PROTECT `session-log.md`
as the narrative spine.

## Acceptance criteria

- [ ] `campaign-memory` RAG collection built from the campaign's own history, refreshed on save.
- [ ] `dm-recall` returns relevant prior events on scene entry (been-here / met-them / promised-this).
- [ ] Tiered memoir: always-on arc summary + recent verbatim + compressed older + retrievable archive.
- [ ] book-canon vs our-story provenance dimension keeps the large imported world out of always-loaded context.
- [ ] `session-log.md` remains the canonical narrative ledger (read, not replaced).
- [ ] Test: a recall query for a past DCC event returns the right memory.

## Verification

Lane: agent

## Blocked by

story-spine-context, embeddings-coarse-index

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
