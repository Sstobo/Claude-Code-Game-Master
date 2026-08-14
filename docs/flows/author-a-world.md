---
type: Flow
title: Authoring an original world
description: /new-game's six phases — the two mechanisms that stop a generated world from collapsing into generic fantasy, and the passes that make it open alive.
sources:
  - { resource: /.claude/commands/new-game.md }
  - { resource: /lib/world_author.py }
  - { resource: /tools/gm-worldgen.sh }
  - { resource: /.claude/agents/world-author.md }
  - { resource: /.claude/agents/world-kit-author.md }
  - { resource: /.claude/agents/world-reconciler.md }
  - { resource: /lib/plot_spine.py }
  - { resource: /lib/clock_seed.py }
  - { resource: /lib/opening_seed.py }
  - { resource: /lib/player_manager.py }
  - { resource: /lib/identity_onboarding.py }
generated: { by: cursor-grok-4.6, at: 2026-08-14T19:15:42Z }
---

# Authoring an original world

`/new-game` is `/import` with the book replaced by generation. The grounding half is
literally the same code: authored canon is compiled into one document and fed through
`gm-extract.sh prepare`, the identical path a PDF takes. Everything upstream of that is
about one problem — **any model asked for "a fantasy world" produces the same world** —
and two mechanisms are aimed at it.

## Phases

| Phase | What happens | Concurrency |
|---|---|---|
| **A — Seed** | genre-aware questionnaire → `world-seed.json`, including an **adaptive axis list** | serial |
| **B — Skeleton** | the world's spine authored in one pass while the seed is fresh, then **shown to the user for approval** | serial |
| **C — Fan-out** | one `world-author` per axis + one `world-kit-author` | **parallel** |
| **D — Reconcile** | `world-reconciler` runs three checks, emits `reconcile-report.json` | serial |
| **E — Ground** | consolidate → compile-canon → `gm-extract.sh prepare` → confirm bible → `campaign-rules` → `spine` → `seed-clocks` → `seed-opening` (provisional) → validate | serial |
| **F — Handoff** | overview, session log, lock the chronicler + art style, hand to the three-door `onboard`. `onboard` re-seeds the opening to match the PC (first `set` does the same after `/create-character` `save-json`) | serial |

## The fan-out is race-free by file ownership, not by locking

Every `world-author` writes **only** `canon/<axis>.md` and `authored/<axis>.json`. No two
agents touch the same file, so N agents can run simultaneously with no coordination. The
merging is then done by one single-threaded pass — `gm-worldgen.sh consolidate` — which
folds every `authored/*.json` into `locations.json` / `npcs.json` / `plots.json` /
`facts.json` and the bible, deduping graph fragments as it goes.

This is the same pattern [importing a book](import-a-book.md) uses for its four extractors.
When adding a new axis, the contract to preserve is *the axis owns its two files* — an
author that writes to campaign root reintroduces the race.

Consolidation **preserves the bible's `confirmed` flag** (`lib/world_author.py:229`), which
is what lets Phase E confirm explicitly rather than having a merge silently mark an
unreviewed world playable. See [the World Bible](../modules/world-bible.md).

## An authored world has to open alive, not just exist

A world can be fully authored and still open dead — that was the state before Phase E
ran the seeding passes: `plots.json` did not exist (so STORY THREADS was empty), there
was no arc, no clock ticking, `player_position.current_location` was null and the rules
block was blank. The fix is not new machinery; it is running the passes an import
already runs, in the same order, over authored plots instead of extracted ones.

That starts at consolidation. Each `authored/<axis>.json` may carry a `plots` object
keyed by name and typed per `schemas.PLOT_TYPES`, and `_merge_plots`
(`lib/world_author.py`) folds them into `plots.json` name-deduped, existing entries
winning — the same shape as the locations/NPC merges, so a re-run never resets a
plot's status or events. An axis with no `plots` key is untouched by it.

Everything downstream reads that file, which is why the order in Phase E is not
arbitrary: `spine` writes the arc, and both `seed-clocks` and `seed-opening` read what
it wrote (`lib/opening_seed.py` opens on `overview.story_spine.arc[0]`, falling back to
the first `main` plot). A world whose axes authored no `main` plot has no arc to open
on, and `seed-opening` says so rather than guessing.

That Phase E seed is **provisional** — the world has to stand somewhere before a
hero exists, but standing is not having already played. `seed-opening` writes a
location, `overview.opening_hook`, and a `plot_local` KEY FACT the first brief
already prints; it does not fabricate a session-log beat or stamp a plot `active`.
Phase F still hands off to the three-door question; location + hook are rewritten
when the PC first exists (`gm-player.sh onboard`, or the first `gm-player.sh set`
if they rolled a sheet via `/create-character` `save-json`), so a pirate-era sheet
does not inherit a king-era hook. Reseed picks the matching plot; it does not
start it. A later `set` after a PC-matched opening (`opening_matched_to_pc`)
leaves it.

`campaign-rules` is the odd one out: it derives the overview's `campaign_rules` from
the bible's `signature_systems`, not from plots, so it can run anywhere after the
bible is confirmed.

## The two anti-generic mechanisms

**1. The adaptive axis list (Phase A).** The seed picks which dimensions matter for *this*
genre rather than filling a fixed template — a sword-and-sorcery world gets deep
blood-magic lore and a stub for technology; a sci-fantasy world inverts that. A fixed axis
list is what produces the same five elemental kingdoms every time.

**2. The reconciler (Phase D).** Three checks, and only one of them is about prose:

- **genericness critic** — flags anything that could have come from any generic fantasy
- **kit ↔ flavor agreement** — does `ruleset.json` actually *play* like the world reads?
- **graph cross-link** — weave the independently-authored axes together

The second check is the one that matters most and is easiest to skip. A world can read as
distinctive and still play as generic d20 if the kit author defaulted. The reconciler's
`verdict: needs-changes` is a real gate: re-run the relevant author or patch the authored
files, then re-reconcile. Applying only the low-risk cross-link edits and moving on leaves
the genericness flags in the world.

## Where it differs from an import

- No source text exists, so the bible's voice block is **authored**, not filtered against
  the source — the verbatim grounding check in `draft_voice` has nothing to check against.
- The chronicler and art style are locked here, at world creation, from the seed's
  `art_style` / `chronicler_*` fields. They are explicitly **not** an in-play improvisation.
  See [scene illustration](scene-illustration.md).
- `ruleset.json` is authored by the `world-kit-author` agent in Phase C, not drafted from
  the bible by `draft_ruleset_from_bible` — which is why an original world can have a
  genuinely non-d20 progression model while an import defaults to milestone. Only the
  overview's `campaign_rules` block is derived from the bible, by the same
  `gm-extract.sh campaign-rules` verb import uses.

## Related

- [Game core and World Kit](../modules/game-core-and-world-kit.md) — what `ruleset.json` must declare
- [RAG stack](../modules/rag-stack.md) — what `prepare` does with the compiled canon
