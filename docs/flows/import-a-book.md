---
type: Flow
title: Importing a book
description: How a PDF becomes a playable campaign — parallel extraction, then a strictly-ordered sequence of repair and seeding passes.
sources:
  - { resource: /.claude/commands/import.md }
  - { resource: /.claude/agents/extractor-npcs.md }
  - { resource: /tools/gm-extract.sh }
  - { resource: /lib/agent_extractor.py }
  - { resource: /lib/campaign_manager.py }
  - { resource: /lib/extraction_cap.py }
  - { resource: /lib/plot_spine.py }
  - { resource: /lib/clock_seed.py }
  - { resource: /lib/opening_seed.py }
generated: { by: claude-opus-5, at: 2026-08-13T21:19:33Z }
---

# Importing a book

`/import` is a long orchestration where the model drives and the tools stay deterministic.
The pattern is **parallel author → serial normalize**: four extractor agents read the book
concurrently and write to separate files, then a single-threaded chain of passes folds
their output into runtime state. That split is what keeps the fan-out race-free.

## The shape

1. **`prepare`** — extract text, chunk it, build the vector index — then **`gm-campaign.sh
   switch` immediately**. Every RAG read downstream resolves against the *active*
   campaign's vector store, so the switch has to precede the preview and the agents, not
   trail them at the summary step. The command asserts the switch took (`gm-campaign.sh
   active` equals the expected slug) and stops the import on a mismatch — a silent failure
   here has all four agents extracting the *previous* campaign's book.
2. **Preview** — sample RAG queries, shown to the user so they can see what the book yields
   before committing.
3. **Four extractor agents in parallel** — `extractor-npcs` / `-locations` / `-items` /
   `-plots`, each writing `extracted/<type>.json`. They are launched simultaneously and
   share no files. Each finds its material through `gm-search.sh --rag-only` queries rather
   than reading `chunks/` wholesale, which is why step 1's switch is load-bearing. Their
   prompts live in the **markdown body** of `.claude/agents/extractor-*.md`; the agent
   loader reads the body and ignores unknown frontmatter keys, so a prompt parked in
   frontmatter never reaches the agent.
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
| `normalize` | copy `extracted/*.json` to the campaign root, unwrapping agent wrappers; unify `location_tags` → `tags.locations` | agents finished |
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
- A punctuated campaign name ("Baldur's Gate: Book 1") splitting across two directories.
  A **new** name gets its folder from one rule everywhere — `CampaignManager._slugify`
  (`lib/campaign_manager.py`), used by campaign creation and by extraction, exposed to shell
  as `campaign_manager.py slugify`. Never re-implement it in a `tr | sed` pipeline. It also
  never returns empty — a name with no ASCII alphanumerics ("龍の伝説") gets a deterministic
  `campaign-<hash>` slug, because an empty slug joined onto `campaigns/` is what an
  `rm -rf` in `gm-extract.sh clean` would read as *every* campaign. A shell caller that needs
  an **existing** directory does not slug at all: it asks `campaign_manager.py resolve`
  (every `gm-extract.sh` verb that needs one does), which routes through `_resolve_name` /
  `_resolve_in` and matches against what is on disk. That is what keeps folders created under
  the older, looser rule (`baldur's-gate`, `curse_of_strahd`) reachable — re-slugifying
  `curse_of_strahd` yields `curse-of-strahd` and reports a real campaign as missing. Nothing
  on disk is renamed. Resolution only ever returns a **direct child** of `campaigns/`:
  slugging used to make `clean "../rag"` impossible by stripping slashes, and matching real
  folder names has to refuse paths explicitly instead — `campaigns/../rag` is a directory,
  and `rm -rf` does not care that it sits outside the campaign tree.
- `integrity` failing strict: read its unresolved list. Each entry names the owner and the
  reference; the fix is almost always a missed `reconcile` or an out-of-order run, not a
  bad extraction.

## Related

- [RAG stack](../modules/rag-stack.md) — what `prepare` builds and `enhance` queries
- [Authoring a world](author-a-world.md) — the same grounding machinery, no book
