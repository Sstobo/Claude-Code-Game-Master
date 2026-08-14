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
  - { resource: /lib/book_bible.py }
  - { resource: /lib/world_bible.py }
  - { resource: /lib/extraction_cap.py }
  - { resource: /lib/minor_stubs.py }
  - { resource: /lib/location_reconcile.py }
  - { resource: /lib/plot_spine.py }
  - { resource: /lib/clock_seed.py }
  - { resource: /lib/opening_seed.py }
generated: { by: claude-opus-5, at: 2026-08-14T12:21:54Z }
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
   large-span reads rather than chunks, and strictly in that order because each step
   reads the one before it (below). See [the World Bible](../modules/world-bible.md).
6. **`gm-enhance.sh batch`** — RAG enrichment of every **active** entity. Marked "critical
   for quality" in the command, and it is: this is what fills NPC `context` with real
   dialogue. `EntityEnhancer.list_unenhanced` skips `background: true` entities, which is
   what keeps tiering-instead-of-deleting from multiplying the enhancement bill by the
   size of the book's walk-on cast; a background entity is enhanced when it is promoted.

## The chain is ordered, and the order is load-bearing

Run these out of sequence and the strict gate fails on references an earlier pass would
have repaired:

| Pass | Does | Depends on |
|---|---|---|
| `normalize` | copy `extracted/*.json` to the campaign root, unwrapping agent wrappers; unify `location_tags` → `tags.locations` | agents finished |
| `cap` | rank each type; top-N stay active, the rest get `background: true` | normalize |
| `fix-items` | clear lore-only cursed flags, reclassify wondrous, null non-price values | cap |
| `normalize-connections` | canonicalize `connections[].to`; move rule-phrases into `notes` | cap |
| `reconcile` | stub unresolved location references (`low_confidence`); drop only a dead connection edge whose target is routing prose | connections normalized |
| `stub-npcs` | stub plot-referenced NPCs extraction never produced | cap |
| `stat-npcs` | assign difficulty-tier proxy stats, flag non-combatants statless | NPC set final |
| `integrity` | canonicalize every cross-reference; **strict-fail on unresolved** | all repairs done |
| `spine` | order main plots into an arc by source position | plots final |
| `seed-clocks` | seed threat clocks from time pressure in plot text | spine |
| `seed-opening` | set starting position + opening beat + session-log hook | spine |
| `archive` | move `extracted/` aside | everything |

The passes most likely to surprise:

- **`cap` tiers, it does not delete.** Every entity the agents extracted stays in
  `npcs.json` / `locations.json` / `items.json` / `plots.json`; the ones ranked below the
  limit are rewritten in place with `"background": true`. The pipeline must not pre-make
  the creative decision of who exists in the world — a walk-on the book named is still a
  person the GM can pull into a scene. Because nothing leaves the file, no cross-reference
  is orphaned by capping, and `reconcile` / `stub-npcs` repair only what extraction
  genuinely missed. See [the entity graph](../modules/entity-graph.md).
- **Importance is book-agnostic on purpose.** `extraction_cap` scores by source mention
  frequency, plus a large boost for being referenced by a plot, plus a party-member boost.
  No name is hardcoded, which is what guarantees the main cast is active in any book: the
  main cast is precisely who the main plots reference. Plots rank by their canonical type's
  priority, read from `schemas.PLOT_TYPE_SORT` — so `threat` and `mystery` outrank `side`
  and `optional` instead of falling to the unknown-type floor, as a local hardcoded weight
  table used to make them. The cap also maps `PLOT_TYPE_SYNONYMS` itself, because
  `validate_plot_types` runs a pass later in `stub-npcs`: a plot the agent typed
  "main quest" arrives here raw, and ranking it raw files the book's spine below an errand.
- **`reconcile` keeps places it cannot verify.** A reference that resolves to no node
  becomes a stub flagged `low_confidence: true` rather than a deletion: "the book named
  this, nobody has checked what it is" is a judgment for play, not for a shape heuristic.
  The one thing still dropped is a **connection target** that states a routing rule instead
  of a destination ("Transfer stations ending in 1"), and each dropped name lands in
  `facts.json` under `dropped_references`. The same string arriving from a plot or an NPC
  tag is stubbed, not dropped — "The Upper Level of the Tower of the Elephant" and
  "Kandahar via the Zhaibar Pass" are places, and a phrase test run over them deletes real
  geography.

## The identity chain hangs off one file

`world-bible.json` is written first and everything downstream derives from it, through
three `gm-extract.sh` verbs that wrap `lib/book_bible.py`:

| Step | Verb | Reads | Writes |
|---|---|---|---|
| bible | `draft-bible` | `current-document.txt` | `world-bible.json` (`confirmed: false`) |
| kit | `draft-ruleset` | the bible | `ruleset.json` |
| overview | `campaign-rules` | the bible's `signature_systems` | `campaign-overview.json` → `campaign_rules` |
| voice | `draft-bible --voice-json` | the bible + source | the bible's `voice` block |

Three things about that chain:

- **The bible is drafted, not generated.** `draft-bible` writes only what the source
  proves — the chapter map, the verbatim-filtered voice, the skeleton keys — and the
  model authors tone/themes/factions/geography/signature systems into it by re-running
  the same verb with `--fields-json`. It is idempotent and refuses a confirmed bible, so
  a re-run never flattens authorship.
- **The kit is derived, not pasted.** `draft-ruleset` takes the attribute list,
  progression model and `kit` router from the importer and everything else from the
  bible. `kit: dnd5e` is reserved for books that genuinely are D&D modules; it is what
  puts `spell-caster` in `active_agents`. It refuses to overwrite an existing
  `ruleset.json`, which is what makes the "copy a sibling book's kit" path safe.
- **The world is not the player's until they say so.** The draft carries
  `confirmed: false`; `world_bible.py review` prints it and `world_bible.py confirm`
  stamps it, after the user approves. `/import` never confirms on their behalf.

If `draft-bible` fails, the whole tail fails — the kit, the campaign rules and the voice
pass all read the bible. The two real failures are a missing `current-document.txt` (a
`prepare` that did not finish) and an already-confirmed bible.

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
