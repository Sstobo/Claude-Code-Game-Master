---
slug: recall-pushed-into-context
title: The world volunteers its memory — push recall and open debts into every scene
category: feature
kind: afk
priority: p0
lane: agent
parentPrd: make-the-world-remember
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-14T02:25:26Z
updatedAt: 2026-08-14T02:25:26Z
---

## Parent

Make the World Remember (prds/make-the-world-remember.md)

## Category

feature

## What to build

`CampaignMemory` is a complete long-term memory — embeddings over arcs, session summaries
and facts, cosine recall with a keyword fallback — with **zero automated callers**.
`recall()` (`lib/campaign_memory.py:132`) and `memoir()` (`:207`) fire only when the GM
model chooses to ask, which requires already suspecting there is something to remember.
`refresh()` runs on every autosave, so the index is current and unread.

The scene brief already knows what the scene is *about* — the current location and who is
present. That is a query. Ask on the model's behalf.

Add one block to `get_full_context` (`lib/session_manager.py:411-733`), sited near
PREVIOUSLY ON:

1. **THE WORLD REMEMBERS** — `CampaignMemory.recall()` seeded from live scene state:
   current location plus the names of present NPCs (reuse the presence list the brief
   already computes rather than recomputing it).
2. **OPEN DEBTS** — `open_debts` from the most recent arc entry
   (`lib/campaign_memory.py:72-84`), currently stored, embedded and read by nothing.
   This is the field that carries "you promised the innkeeper".
3. Bound the block like every other one (a few entries; `full` lifts it), and disclose the
   remainder rather than silently truncating, matching how the party block reports
   `... and N more`.
4. Wrap the whole thing in the degrade-to-empty pattern `SceneContext.build` uses for RAG
   (`lib/scene_context.py:56-64`): a missing `campaign-memory.json`, absent embedding deps,
   or any error inside recall produces an empty block, never a traceback in the middle of a
   session. Context must still build for a campaign that has never been saved.

## Acceptance criteria

- A campaign with an arc entry whose `open_debts` names a present NPC shows that debt in
  `gm-session.sh context` with no explicit `gm-recall.sh` call anywhere.
- Recalled entries relevant to the current location appear in the brief.
- Deleting or corrupting `campaign-memory.json` still yields a complete context (block
  simply absent), and a never-saved campaign does not error.
- The block respects `--full` and discloses what it held back.
- `DM_DEBUG_CONTEXT=1` token cost stays within a sane budget — report the before/after in
  the ticket resolution.
- `docs/modules/scene-context.md` and `docs/modules/campaign-memory.md` updated and
  restamped in the same commit. `campaign-memory.md:105` currently states "previously on is
  built from session-log.md directly, not from this index" and `:78` says `memoir()` has no
  caller — both become wrong here.

## Notes

`advisory-fences` (in `ready/`) owns exposing `--top-k` on the recall CLI. Do not duplicate
that; if this block needs a different k, pass it as an argument to `recall()` in-process.
