---
type: Module
title: Campaign memory and the Loremaster
description: How a long campaign remembers itself — a keyword recall index over lived history, and a separate cached deep-read over the source book.
sources:
  - { resource: /lib/campaign_memory.py }
  - { resource: /lib/loremaster.py }
  - { resource: /tools/gm-recall.sh }
  - { resource: /tools/gm-lore.sh }
generated: { by: claude-fable-5, at: 2026-08-13T14:25:55Z }
verified: { by: claude-fable-5, at: 2026-08-13T14:16:30Z }
---

# Campaign memory and the Loremaster

Two memories, easily confused, with different subjects:

| | `CampaignMemory` (`gm-recall.sh`) | `Loremaster` |
|---|---|---|
| Remembers | **what we did** — session summaries + facts | **what the book says** — chapters of the source text |
| Backed by | keyword overlap over `campaign-memory.json` | the coarse chapter index over the retained book text |
| Front door | `gm-recall.sh` | `gm-lore.sh "<location>" [--important]` (wrapper added 2026-08-13; had no caller before that) |

Neither uses embeddings. The vector store is a third, separate thing —
see [RAG stack](rag-stack.md).

## Recall is keyword overlap, not semantics

`recall()` scores by counting shared word tokens between the query and each entry
(`lib/campaign_memory.py:78-88`). The docstring's "semantic-ish" means *not semantic*.
Practical consequence: recall finds an event only if the query reuses its **words**.
Asking "have we met the clown before?" will miss a summary that says "Grimaldi". Query
with names and nouns from the fiction, not paraphrase.

`session-log.md` remains the canonical ledger; this module only reads it. It parses on the
`## Session Started:` / `### Session Ended:` markers and skips `**`-prefixed footer lines,
so a hand-edited log that loses those markers loses its history silently.

## `refresh` runs on save, and only on save

`tools/gm-session.sh:153` calls `campaign_memory.py refresh` inside the **save** path,
with errors swallowed (`|| true`). So the recall index is a snapshot as of the last save,
not live state — and a campaign that has never been saved recalls from a fresh `gather()`
every time instead (`recall()` falls back to `gather()` when the file is absent).

The Stop hook autosaves every turn ([persist before narrate](../conventions/persist-before-narrate.md)),
which is what keeps this from mattering in normal play.

## Provenance is decided by two category names

`_CANON_CATEGORIES = {"plot_world", "world_building"}` (`lib/campaign_memory.py:23`) is
the entire book-canon / our-story split. A fact filed under any other category is
"our-story" regardless of where it came from, and session summaries are always our-story.
Filing an imported book fact under, say, `lore` therefore mislabels it — and
`--provenance book-canon` will not find it.

## `memoir()` is thinner than it sounds

`arc_summary` is the **most recent session entry truncated to 300 characters**, not a
synthesized arc, and `compressed_older` is a *count* of older entries, not compressed
text (`lib/campaign_memory.py:90-102`). The consolidation the docstring describes is a
shape the data supports, not work this module performs. Anything that needs a real arc
summary has to generate it.

## The Loremaster re-indexes the whole book per instance

`Loremaster.__init__` loads the campaign's book text and calls `index.build(text)` every
time it is constructed (`lib/loremaster.py:29-31`). There is no persisted index, so
construction cost scales with book size — which is why `gm-lore.sh` is an on-demand call
for new/important scenes, not something wired into every context load. It reads `current-document.txt` or
`book-text.txt` from the campaign directory — both are gitignored, so a cloned campaign
has no book text and every brief comes back with empty chapters.

The gate is the point of the module: a cached location that is not flagged `important`
returns immediately with no read. Note what a deep read actually returns —
the chapter is loaded and token-logged in full, but `grounded_excerpt` is the **first 500
characters** (`lib/loremaster.py:63`). The large span is for the model call the /gm flow
makes; this module hands back a pointer and a taste.

## Related

- [Scene context](scene-context.md) — "previously on" is built from `session-log.md` directly, not from this index
- [RAG stack](rag-stack.md) — the third memory, over embedded source chunks
