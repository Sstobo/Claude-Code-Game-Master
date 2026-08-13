---
slug: state-of-the-table
title: State of the Table — repair sprint + executable World Kit
status: active
version: 1
supersedes: null
createdAt: 2026-08-13T15:45:00Z
updatedAt: 2026-08-13T15:45:00Z
---

## Problem Statement

The 2026-08-13 six-reader audit ("State of the Table", claude.ai artifact
6309fdcb) found that (a) several core workflows are broken today — `/import`
cannot produce a playable campaign, `gm-reset.sh archive` destroys data,
startup can greet the player with a traceback, imports flatten threat/mystery
plots, save/restore fabricates history — and (b) the product's core promise,
"each book plays as its own game", is not yet true: the World Kit is authored
and documented but almost nowhere consumed (resolution model unread, vitals
untracked, signature systems dead data, character creation hardcoded 5e,
identity onboarding implemented with zero callers).

## Solution

Two tiers of work. Tier 0: repair every verified breakage so a punctuated-name
book imports end-to-end, resets are safe, startup never stack-traces, plots
keep their types, and saves round-trip whole. Tier 1: make the kit executable
and ambient — resolution/vitals/signature-systems consumed by the engine and
surfaced in scene context, onboarding and character creation kit-aware, one
presence resolver, and /new-game reaching parity with /import's finishing
passes.

## User Stories

1. As a player, I want `/import "Book: Subtitle"` to produce a playable campaign with NPCs, locations, and correctly typed plots, so my book actually becomes a game.
2. As a player in a non-D&D world, I want checks, vitals, rules, and character creation to follow my world's kit, so the world plays distinct instead of reading distinct.
3. As a player, I want resets, saves, and restores to never lose or fabricate state.
4. As the GM agent, I want the kit, presence, and rules ambient in scene context so I never re-derive or guess them.

## Implementation Decisions

- Extractor agent prompts move from `instructions:` frontmatter into the markdown body (loader contract).
- `/import` switches the active campaign immediately after `prepare`; one slug function (`CampaignManager._slugify`, hardened) used by campaign create, extractor sanitize, and `gm-extract.sh`.
- `world-bible.json` is authored before kit derivation; `draft_ruleset_from_bible` + `bible_to_campaign_rules` replace the generic ruleset heredoc in import.md.
- `gm-reset.sh archive` becomes a directory copy under `world-state/archive/`; destructive commands gain `--yes` and `[ -t 0 ]` gates; no git branches.
- `require_active_campaign` added to gm-session/enhance/extract/worldgen; CLAUDE.md startup tree gains the "campaigns exist, none active" branch.
- One `PLOT_TYPES` constant in `schemas.py`, imported everywhere; off-enum values mapped, never flattened.
- Save snapshots cover all stateful campaign files, carry `save_version`, and autosaves rotate (keep last N).
- `game_core.resolve_check` dispatches on the kit's `resolution_model`; PlayerManager tracks vitals from `stat_schema.vitals`, drops hardcoded level-20s, gates `_normalize_xp` on the progression model; `get_xp_status` becomes read-only.
- Scene context gains a KIT block (name, resolution, progression, vitals, skills) and renders rules from `WorldKit.signature_systems()` with `campaign_rules` fallback; the three STEP-0 skill guards collapse to context deference.
- `gm-player.sh onboard --mode canon|original|nameless` wraps `identity_onboarding.py`; both pipelines and the no-character branch route to it; `/create-character` splits into a kit-generic spine + 5e branch.
- One presence/entity resolver module used by scene context, consequence tick, and search.
- `/new-game` Phase E runs spine, seed-clocks, seed-opening; axis authors emit plots; `campaign_rules` derived from the bible.

## Testing Decisions

- Regression test: punctuated campaign name lands in exactly one directory.
- Wrapper-level tests (run from a non-repo cwd) for the persist-path tools.
- Milestone-progression path gets its first tests (no phantom XP objects).
- A test asserting both context doors agree on presence.
- Save round-trip test: snapshot → mutate → restore → deep-equal all stateful files.
- Enum test replaces `tests/test_minor_stubs.py`'s wrong assertion.
- All agent-lane; no manual QA required in these tiers.

## Out of Scope

Tier 2 and Tier 3 of the report: `--json` wrapper unification, `gm-roll.sh`,
relative time/rest routes, session-end reconciliation, shard extraction and the
resumable import driver, grounding front-door swap, CLAUDE.md diet, docs and
help-text reconciliation, dead-code sweep, mobile pass. These get their own PRD
after the kit is real.

## Further Notes

Full evidence with file:line references in the published audit artifact and the
six reader reports (this session, 2026-08-13). OKF: update claiming docs in the
same commit as code per repo convention; `docs/flows/import-a-book.md` and
`docs/flows/onboarding-and-death.md` are known-stale and must be restamped by
the tickets that touch their subjects.
