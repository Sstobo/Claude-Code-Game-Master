---
type: Flow
title: Authoring an original world
description: /new-game's five phases — and the two mechanisms that stop a generated world from collapsing into generic fantasy.
sources:
  - { resource: /.claude/commands/new-game.md }
  - { resource: /lib/world_author.py }
  - { resource: /tools/gm-worldgen.sh }
  - { resource: /.claude/agents/world-author.md }
  - { resource: /.claude/agents/world-kit-author.md }
  - { resource: /.claude/agents/world-reconciler.md }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
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
| **E — Ground** | consolidate → compile-canon → `gm-extract.sh prepare` → confirm bible → validate | serial |
| **F — Handoff** | overview, session log, lock the chronicler + art style, hand to character creation | serial |

## The fan-out is race-free by file ownership, not by locking

Every `world-author` writes **only** `canon/<axis>.md` and `authored/<axis>.json`. No two
agents touch the same file, so N agents can run simultaneously with no coordination. The
merging is then done by one single-threaded pass — `gm-worldgen.sh consolidate` — which
folds every `authored/*.json` into `locations.json` / `npcs.json` / `facts.json` and the
bible, deduping graph fragments as it goes.

This is the same pattern [importing a book](import-a-book.md) uses for its four extractors.
When adding a new axis, the contract to preserve is *the axis owns its two files* — an
author that writes to campaign root reintroduces the race.

Consolidation **preserves the bible's `confirmed` flag** (`lib/world_author.py:197`), which
is what lets Phase E confirm explicitly rather than having a merge silently mark an
unreviewed world playable. See [the World Bible](../modules/world-bible.md).

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
- The kit is derived from the world by a dedicated agent rather than drafted from a bible
  by `draft_ruleset_from_bible`, which is why an original world can have a genuinely
  non-d20 progression model while an import defaults to milestone.

## Related

- [Game core and World Kit](../modules/game-core-and-world-kit.md) — what `ruleset.json` must declare
- [RAG stack](../modules/rag-stack.md) — what `prepare` does with the compiled canon
