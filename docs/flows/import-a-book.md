---
type: Flow
title: Importing a book
description: Index the book, ask who they are, open one stage. The rest stays in the binder until play walks toward it.
sources:
  - { resource: /.claude/commands/import.md }
  - { resource: /tools/gm-extract.sh }
  - { resource: /lib/campaign_manager.py }
  - { resource: /lib/book_bible.py }
  - { resource: /lib/world_bible.py }
  - { resource: /lib/opening_seed.py }
  - { resource: /lib/identity_onboarding.py }
  - { resource: /lib/session_manager.py }
  - { resource: /lib/play_pack.py }
  - { resource: /tools/gm-playpack.sh }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T16:10:00Z }
---

# Importing a book

`/import` puts a book on the GM's chair and opens a door. It does not finish a
database of the book. The invariant lives in [the dream](../conventions/the-dream.md):
the campaign file is a journal; the book is the world.

## The shape

1. **`prepare` + immediate `switch`.** Extract text, chunk it, build the vector
   index, then make the campaign active. Every later RAG read
   (`gm-search.sh --rag-only`, `gm-lore.sh`, `gm-context.sh`) resolves against
   the *active* store. Assert the switch (`gm-campaign.sh active` matches the
   slug). A silent mismatch here grounds the opening in the wrong book — or none.
2. **The door.** Ask who they are, or who they came to meet. Do not preview
   entity counts. Do not run the extractors *as a census* (full records) — their
   one sanctioned use is the light one-sentence World Index (Step 5.5).
3. **World identity.** Bible → kit → campaign_rules → voice → chronicler. Tone
   and how the holodeck *sounds*. Horizon names, not a gazetteer. The player
   confirms the bible; `/import` never confirms on their behalf.
4. **The stage.** One room, the exits you can see, the people in it, one hook.
   Persist with `gm-playpack.sh set` + `stage`, then `onboard`. Enhance only the
   people in this room. The pack is the opening; `onboard` keeps its room + hook
   (`gm-playpack.sh set` marked it matched) — still not a fake session.
5. **Play.** When someone new walks on, `gm-playpack.sh from-book "<name>"`, then
   RAG, then narrate. `move` already creates a blank destination; first visit
   already fires a lore brief.

## Why the switch is load-bearing

`prepare` can create the folder; tools read `active-campaign.txt`. Switch late
and the stage is built from the previous campaign's book, or from nothing.
Compare slugs, not display names. Resolve the directory with
`gm-campaign.sh path` — never hand-build `world-state/campaigns/<display-name>`.

## Why identity precedes the stage

A book has more than one first page. King-era Conan and corsair-era Conan are
different rooms. Spine-position-1 as a universal opening is a lie. The
protagonist picks the page; the stage is built from that page.

## World identity is not inventory

`draft-bible` writes what the source can prove (the empty World Index scaffold,
verbatim voice filter, skeleton keys — as of 2026-08-15 it no longer persists a
chapter map; `segment_into_chapters` now feeds only the RAG coarse index). The
model authors tone / themes / a *handful* of factions and places. `draft-ruleset` takes attributes, progression, and `kit`
from the importer — `dnd5e` only when the file is a D&D module. Signature
systems live in the bible and map into `campaign_rules`. A missing
`current-document.txt` means `prepare` did not finish; an already-confirmed
bible refuses a silent overwrite.

## Leftover census machinery

`gm-extract.sh` still exposes `normalize`, `cap`, `reconcile`, `stub-npcs`,
`integrity`, and the four extractor agents. Using them to build **full records**
front-loads a closed graph so integrity can pass — including stubs for `the
desert` and walk-ons a plot string named. **`/import` must not run the census.**
The extractor agents do have one sanctioned use: the light one-sentence **World
Index** (`gm-extract.sh write-index`, capped at 6 agents) — a scannable roster of
what exists, pointers not records. Operators repairing a legacy gazetteer import
use [the operations guide](../import-guide.md).

`integrity` failing strict on unresolved names is the old product saying the
wiki is incomplete. The new product says those names are not on stage yet.

## Where an import goes wrong

- A punctuated campaign name splitting across two directories — slug via
  `campaign_manager.py slugify`; resolve existing folders via `resolve`, never
  a `tr | sed` pipeline. See the same landmine in older notes: an empty slug
  joined onto `campaigns/` is what `clean` would read as every campaign.
- Agents validating against a live campaign file — see
  [extraction vs runtime schema](../gotchas/extraction-vs-runtime-schema.md)
  (legacy extractors only).
- Silent entity loss at a merge — see
  [wrapped vs unwrapped](../gotchas/wrapped-vs-unwrapped-merge.md) (legacy).

## Related

- [The dream](../conventions/the-dream.md)
- [RAG stack](../modules/rag-stack.md) — what `prepare` builds
- [Authoring a world](author-a-world.md) — same shelf, authored canon instead of a PDF
