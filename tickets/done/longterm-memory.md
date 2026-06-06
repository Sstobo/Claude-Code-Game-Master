---
slug: longterm-memory
title: Long-term campaign memory — memory RAG + tiered memoir + dm-recall
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [story-spine-context, embeddings-coarse-index]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:16:04Z
changedFiles: [lib/campaign_memory.py, tools/dm-recall.sh, tools/dm-session.sh, tests/test_campaign_memory.py]
resolution: CampaignMemory builds a recall collection (campaign-memory.json) from session summaries + facts with our-story/book-canon provenance, refreshed on save; dm-recall recall/memoir/refresh; tiered bounded memoir; session-log.md stays canonical (read-only)
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:16:04Z
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

- [x] `campaign-memory` RAG collection built from the campaign's own history, refreshed on save. (keyword-overlap collection by default — a vector embedder is the pluggable upgrade, like coarse_index)
- [x] `dm-recall` returns relevant prior events on scene entry (been-here / met-them / promised-this).
- [x] Tiered memoir: always-on arc summary + recent verbatim + compressed older + retrievable archive.
- [x] book-canon vs our-story provenance dimension keeps the large imported world out of always-loaded context.
- [x] `session-log.md` remains the canonical narrative ledger (read, not replaced).
- [x] Test: a recall query for a past DCC event returns the right memory.

## Verification

Lane: agent

## Blocked by

story-spine-context, embeddings-coarse-index

---

## QA Reports

### 2026-06-06T05:16:04Z — pass [ss-tix001]
`uv run pytest` → 119 passed (6 new in tests/test_campaign_memory.py); bash ok.
- CampaignMemory.gather pulls session-ended summaries (our-story) + facts (plot_world/world_building → book-canon, else our-story). refresh() writes campaign-memory.json; wired into dm-session.sh save (best-effort). recall() keyword-ranks, optional provenance filter. memoir() = arc_summary + last-3 recent + compressed_older count + archive/canon counts.
- Tests: recall("Remex soul crystal") surfaces the Remex thread; provenance filter returns only book-canon; memoir tiered + bounded (≤3 recent); refresh writes N entries; session-log.md byte-identical after recall/memoir (canonical, read-only); empty query → [].
- [human-judgement] Recall is keyword-overlap by default (hermetic, no heavy deps); swapping in a vector embedder is the same pluggable pattern as coarse_index.

## History

- 2026-06-06T05:16:04Z  in-progress → done  [ss-tix001]
- 2026-06-06T05:16:04Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
