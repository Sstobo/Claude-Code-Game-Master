---
type: Flow
title: Importing a book
description: How a PDF becomes a playable campaign — parallel extraction, then a strictly-ordered sequence of repair and seeding passes.
sources:
  - { resource: /.claude/commands/import.md }
  - { resource: /tools/gm-extract.sh }
  - { resource: /lib/agent_extractor.py }
  - { resource: /lib/extraction_cap.py }
  - { resource: /lib/plot_spine.py }
  - { resource: /lib/clock_seed.py }
  - { resource: /lib/opening_seed.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# Importing a book

`/import` is a long orchestration where the model drives and the tools stay deterministic.
The pattern is **parallel author → serial normalize**: four extractor agents read the book
concurrently and write to separate files, then a single-threaded chain of passes folds
their output into runtime state. That split is what keeps the fan-out race-free.

## The shape

1. **`prepare`** — extract text, chunk it, build the vector index.
2. **Preview** — sample RAG queries, shown to the user so they can see what the book yields
   before committing.
3. **Four extractor agents in parallel** — `extractor-npcs` / `-locations` / `-items` /
   `-plots`, each reading `chunks/` and writing `extracted/<type>.json`. They are launched
   simultaneously and share no files.
4. **`validate`** then the repair-and-seed chain (below).
5. **Bible → kit → overview → voice → chronicler** — the world's identity, drafted from
   large-span reads rather than chunks. See [the World Bible](../modules/world-bible.md).
6. **`gm-enhance.sh batch`** — RAG enrichment of every entity. Marked "critical for
   quality" in the command, and it is: this is what fills NPC `context` with real dialogue.

## The chain is ordered, and the order is load-bearing

Run these out of sequence and the strict gate fails on references an earlier pass would
have repaired:

| Pass | Does | Depends on |
|---|---|---|
| `normalize` | copy `extracted/*.json` to the campaign root, unwrapping agent wrappers | agents finished |
| `cap` | keep only the top-N per type by importance | normalize |
| `fix-items` | clear lore-only cursed flags, reclassify wondrous, null non-price values | cap |
| `normalize-connections` | canonicalize `connections[].to`; move rule-phrases into `notes` | cap |
| `reconcile` | stub or drop unresolved location references | connections normalized |
| `stub-npcs` | create stubs for plot-referenced NPCs the cap dropped | cap |
| `stat-npcs` | assign difficulty-tier proxy stats, flag non-combatants statless | NPC set final |
| `integrity` | canonicalize every cross-reference; **strict-fail on unresolved** | all repairs done |
| `spine` | order main plots into an arc by source position | plots final |
| `seed-clocks` | seed threat clocks from time pressure in plot text | spine |
| `seed-opening` | set starting position + opening beat + session-log hook | spine |
| `archive` | move `extracted/` aside | everything |

The two passes most likely to surprise:

- **`cap` deliberately breaks the graph.** It keeps the top 30 by importance, which orphans
  references from surviving entities to dropped ones. `reconcile` and `stub-npcs` exist to
  repair exactly that damage — so `cap` must run *before* them, and `integrity` must run
  after. See [the entity graph](../modules/entity-graph.md).
- **Importance is book-agnostic on purpose.** `extraction_cap` scores by source mention
  frequency, plus a large boost for being referenced by a plot, plus a party-member boost.
  No name is hardcoded, which is what guarantees the main cast survives any book: the main
  cast is precisely who the main plots reference.

## Ordering is deterministic, not model judgment

`plot_spine` orders the arc by **earliest chunk position in the source**, not by asking a
model which plot comes first. Same book in, same arc out. `seed-opening` then reads that
arc's first location to decide where the campaign starts, which is why a fresh import opens
on the book's actual opening rather than in a void.

## Where an import goes wrong

- Silent entity loss at the merge — see
  [wrapped vs unwrapped](../gotchas/wrapped-vs-unwrapped-merge.md).
- Agents validating against a live campaign file — see
  [extraction vs runtime schema](../gotchas/extraction-vs-runtime-schema.md).
- `integrity` failing strict: read its unresolved list. Each entry names the owner and the
  reference; the fix is almost always a missed `reconcile` or an out-of-order run, not a
  bad extraction.

## Related

- [RAG stack](../modules/rag-stack.md) — what `prepare` builds and `enhance` queries
- [Authoring a world](author-a-world.md) — the same grounding machinery, no book
