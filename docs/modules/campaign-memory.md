---
type: Module
title: Campaign memory and the Loremaster
description: How a long campaign remembers itself — GM-authored arc entries, an embedding-backed recall index over lived history, and a cached deep-read over the source book.
sources:
  - { resource: /lib/campaign_memory.py }
  - { resource: /lib/loremaster.py }
  - { resource: /tools/gm-recall.sh }
  - { resource: /tools/gm-lore.sh }
generated: { by: cursor-grok-4.6, at: 2026-08-14T18:57:59Z }
verified: { by: claude-fable-5, at: 2026-08-13T14:16:30Z }
---

# Campaign memory and the Loremaster

Two memories, easily confused, with different subjects:

| | `CampaignMemory` (`gm-recall.sh`) | `Loremaster` |
|---|---|---|
| Remembers | **what we did** — arc entries + session summaries + facts | **what the book says** — chapters of the source text |
| Backed by | embeddings over `campaign-memory.json` (keyword fallback) | the coarse chapter index over the retained book text |
| Front door | `gm-recall.sh` | `gm-lore.sh "<location>" [--important]` (wrapper added 2026-08-13; had no caller before that) |

The chunk vector store is a third, separate thing — see [RAG stack](rag-stack.md);
campaign memory keeps its own vectors inside `campaign-memory.json`, not in ChromaDB.

## Recall: semantic when it can be, keyword when it must

Since 2026-08-13, `refresh` embeds every entry via `LocalEmbedder` when the RAG deps are
installed, and `recall()` does cosine top-k over those vectors — so "have we met the
clown before?" can now find a summary that says "Grimaldi". Default top-k is 5;
`gm-recall.sh recall` takes `--top-k` when a scene needs a wider net. Without the deps,
both degrade to the original keyword-overlap path, where recall finds an event only if
the query reuses its **words** — query with names and nouns from the fiction there.

Which path ran is invisible in the output. If recall quality seems paraphrase-blind,
check whether `campaign-memory.json` has an `embeddings` key before blaming the query.
Re-embedding is gated on a content hash of the entry texts, because `refresh` runs on
every autosave and loading the model each turn would be felt.

`session-log.md` remains the canonical ledger; this module only reads it. It parses on the
`## Session Started:` / `### Session Ended:` markers and skips `**`-prefixed footer lines,
so a hand-edited log that loses those markers loses its history silently.

## Recall is pushed, not waited for (since 2026-08-14)

`recall()` had **no automated caller** until now: it fired only when the GM model chose to
ask, which requires already suspecting there is something to remember — the exact failure
this module exists to fix. `SessionManager._world_remembers` now calls it on every context
build, using the scene as the query (current location + present NPC names), and renders a
THE WORLD REMEMBERS block alongside `open_debts` from the latest arc entry. See
[scene context](scene-context.md).

Two consequences worth knowing:

- **The block degrades to nothing, loudly nowhere.** Any failure — absent `campaign-memory.json`,
  missing embedding deps, a half-written index — returns empty and the brief builds without
  it. Same trade as the RAG path: play never stops, and a broken memory looks like a quiet one.
- **Recall's fallback re-gathers the session log**, so its top hits are frequently the very
  summaries PREVIOUSLY ON just printed. `_world_remembers` drops those by normalized
  containment; without that the brief pays twice for the same text.

`memoir()` still has no caller.

## Arc entries are the consolidation tier (since 2026-08-13)

`gather()` can only re-read what the log already says. The **arc entry** is the GM's own
end-of-session synthesis — `{"summary", "who_matters", "open_debts"}` — written with
`gm-recall.sh arc '<json>'` (a bare prose string is accepted as the summary). Session end
prompts for it, and `CLAUDE.md` marks it required: **an arc entry is what makes session 30
feel like a continuation instead of a reboot with notes.** Arcs are preserved across
`refresh` (which used to clobber the whole file) and join the recall index as their own
tier.

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

## `memoir()` leads with real arcs now

`arc_summary` is the latest **GM-authored arc entry** when any exist; the old behavior —
the most recent raw session entry truncated to 300 chars — survives only as the fallback
for campaigns that never wrote one. `compressed_older` is still a *count*, not compressed
text. A campaign whose memoir reads like a truncated sentence is a campaign whose GM has
been skipping the arc step.

## The Loremaster re-indexes the whole book per instance

`Loremaster.__init__` loads the campaign's book text and calls `index.build(text)` every
time it is constructed (`lib/loremaster.py:29-31`). There is no persisted index, so
construction cost scales with book size — which is why `gm-lore.sh` is an on-demand call
for new/important scenes, not something wired into every context load. It reads `current-document.txt` or
`book-text.txt` from the campaign directory — both are gitignored, so a cloned campaign
has no book text and every brief comes back with empty chapters.

The gate is the point of the module: a cached location that is not flagged `important`
returns immediately with no read. Two tiers of output (since 2026-08-13):

- **Default** — pointers + a bounded `grounded_excerpt` (`EXCERPT_CHARS`). This is what
  `gm-session.sh move` auto-runs on the **first visit** to a location when the campaign
  retains book text — the cache gates it, so revisits are silent and the deep read fires
  once per place.
- **`--full`** — the same brief plus `chapter_text`, the *entire* chapter span, for the
  long-context read when the GM actually narrates the place. The full text rides the
  return, never the cache — the book file is the storage.

(Until 2026-08-13 the excerpt was 500 chars and nothing returned the full span, so the
"long-context read" the module was built for had no way to happen.)

## Related

- [Scene context](scene-context.md) — "previously on" is built from `session-log.md` directly; THE WORLD REMEMBERS is what reads this index
- [RAG stack](rag-stack.md) — the third memory, over embedded source chunks
