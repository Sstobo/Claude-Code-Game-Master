---
slug: dm-claude-reimagining
title: DM Claude Reimagining — book-as-its-own-game harness
status: active
version: 1
supersedes: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Problem Statement

DM Claude was built ~1 year ago on a weaker model. It works, but it is a D&D 5e
engine with the chosen book painted on as lore. Six independent expert reviews
converged on the same diagnosis:

1. **Hardcoded to 5e.** XP capped at level 20, character schema requires the six
   5e abilities, ~1196 lines of `CLAUDE.md` are 5e tables. Playing Dune produces
   "d20-fantasy-in-a-desert."
2. **The "living world" has no engine.** `consequence_manager.check_pending()`
   returns the whole active list every turn with zero trigger evaluation;
   `get_full_context` never reads `plots.json`, `facts.json`, or the session log,
   so the DM starts each session knowing party HP but not the plot or last
   cliffhanger. The world only moves when the player looks.
3. **2024 workarounds.** A 1196-line always-on prose interpreter, 19 bash
   wrappers that stdout-scrape, weak MiniLM RAG that deletes the book after
   import, NPCs with no inner life, a 9-step builder gating every entry, combat
   that persists nothing, and zero tests/hooks.

Personal-use only project (no distribution).

## Solution

Re-platform onto modern Claude Code (Skills, subagents, hooks, structured
output, long context, background tasks) around one north star: **drop in a book
you own and play THAT book as its own game on a thin generic core; the world
remembers you and pushes the right thing into the scene at the right beat.**

The system flips from "Claude must remember to look" to "the world pushes
context into Claude's hands." D&D 5e is dropped entirely; a thin generic CORE
(d20-vs-DC resolution, contest/DC ladder, abstract HP/harm + conditions, three
progression frameworks) carries every world, and each imported novel gets a
**bespoke ruleset generated at import** from a structured Book Bible.

## User Stories

1. As a player, I want to import a novel I own and start playing in its world in
   minutes, as that world's own game — not reskinned D&D.
2. As a player, I want NPCs to sound like themselves, want things, and remember
   how I treated them.
3. As a player resuming a campaign, I want the DM to already know the plot, the
   last cliffhanger, and our running gags — no stat-sheet amnesia.
4. As a player, I want consequences I set in motion to fire on their own when I
   return to a place or enough time passes, and the world to keep living between
   sessions.
5. As the developer, I want a test net and structured tooling so I can refactor
   boldly without silently corrupting a 13-session campaign.

## Implementation Decisions

Locked via a 16-question grill. Sequenced in dependency order (Phase 0→5);
encode the phase order as ticket `blockedBy`.

- **Generic CORE (drop 5e):** d20-vs-DC resolution, contest/DC ladder, abstract
  HP/harm + conditions, three configurable progression frameworks
  (`milestone` default, `resource-axis`, `xp-levels`). Thin core — stat names,
  combat feel, progression specifics, signature systems are all bespoke per book.
- **World Kit:** per-campaign `ruleset.json` (stat schema, progression model,
  resolution model, active specialist agents) + a campaign-scoped rules **Skill**
  holding mechanics/prose loaded on demand. `campaign_rules` stays for
  world-flavor systems (loot boxes, viewers).
- **Character schema:** open kit-defined `{identity, vitals, attributes (open
  dict), progression, inventory, conditions}`; validate against active kit; light
  migration shim so the 13-session Dungeon Crawler Carl (DCC) campaign survives
  as the golden fixture + demo. Archive the other two campaigns.
- **Reactivity engine:** hybrid triggers — structured (`trigger_type`:
  on_location / on_npc / on_time / on_event + match + optional expiry) that fire
  and expire automatically, plus a scored free-text fallback. Rewrite
  `check_pending` to evaluate against world state and return only fired items.
  Wire a tick into the move/time flow. Surface 1–2 fired per beat WITH the
  trigger reason so the DM can veto for dramatic timing. Provenance log +
  per-beat snapshot for debuggable/undoable misfires.
- **Context (`get_full_context`):** load the story spine — last 2–3 session-log
  summaries, cliffhanger, active plots from `plots.json`, key facts from
  `facts.json`, recurring gags — plus present-NPC voice/goal/mood. UN-TRUNCATE
  `campaign_rules` (kill the 220-char cut near `session_manager.py:468`). NO
  silent cutoffs anywhere. Soft ~2k-token target as guidance + token tracking
  only; never a hard cut.
- **Tooling:** keep the 19 bash wrappers + Python managers (no MCP, no new
  process) but return structured JSON the model parses — kills stdout-scraping,
  the `bash tools/` prefix/typo class, and the enhance-vs-search confusion.
  Collapse `dm-search` / `dm-enhance query` / `dm-enhance scene` into one
  scene-context call.
- **NPC inner life:** additively add `goal`, `secret`, `current_mood`
  (shifts + persists), `voice` (canonical lines/descriptor), `bonds` (+/-
  relationship values), with defaults so old campaigns load. Add fields
  additively; never reuse the extraction schema for runtime (see MEMORY.md).
- **Import / Book Bible:** stop deleting book text; keep chapter-segmented text,
  read large spans with Opus, emit one structured `world-bible.json` per world
  (voice, tone, themes, factions-as-graph, geography-as-place-graph, timeline,
  signature systems) that auto-drafts the bespoke ruleset + campaign_rules, gated
  by a draft-then-confirm review before play. Demote embeddings to a coarse
  chapter index pointing INTO the text; pluggable embedder. Defer per-scene
  Loremaster until caching is proven.
- **Enforcement:** advisory `PostToolUse` hook (validate/log state writes) +
  `Stop` hook (auto-save session), non-blocking. Currently zero hooks.
- **Combat:** `combat_state.json` (initiative, per-combatant HP/AC/conditions,
  round) + lightweight `dm-combat.sh` (start/add-enemy/hp/condition/next-turn/
  end), OPTIONAL by default (mirror the lightweight-vs-structured dungeon split);
  render the combat header from this state; award XP/loot on end.
- **Onboarding:** identity-first ("Who are you in this world?" → canon character
  lifted from `npcs.json` / original concept / nameless traveler), mechanics
  inferred + persisted silently; full builder opt-in. Collapse the duplicated
  entry menus into one front door; `/dm` is canonical.

## Testing Decisions

- **Tests first (move zero):** pytest golden-file/characterization snapshots of
  `get_full_context` + `check_pending` against the DCC fixture, before touching
  either. Establishes the safety net the rules re-platform depends on.
- Per-kit progression + schema-vs-active-kit validation tests before the World
  Kit refactor. Run across the generic core's three progression frameworks.
- Every additive schema change (character, NPC, consequence, session metadata)
  gets a round-trip load test against the existing DCC campaign specifically.
- Lane `agent` for state/schema/tooling/trigger behavior (assertable in code).
  Lane `manual` for narration feel, onboarding flow, and Book-Bible quality.

## Out of Scope

- Distribution / multi-user / publishing. Personal local tool. Ship zero
  extracted book content in the repo; `.gitignore` it.
- MCP server (explicitly rejected in favor of JSON-returning wrappers).
- Per-scene reflexive long-context chapter reading (deferred behind caching).
- Hard token/latency ceilings (observability only; no silent cutoffs).

## Further Notes

PROTECT in every rewrite: the `campaign_rules` engine, canonical-voice NPC
extraction (verbatim book dialogue in the `context` field), the "Art of Dungeon
Mastering" craft prose, persist-before-narrate + atomic saves, the EntityManager
atomic-JSON layer, `dice.py` as deterministic RNG, the `session-log.md`
narrative ledger, the evangelism-grade README positioning.

God-files to refactor under the kit model once tests exist: `npc_manager.py`
(948), `player_manager.py` (766), `agent_extractor.py` (726).

Recent state: cleanup pass just landed (fixed dice advantage/disadvantage
modifier bug, fixed the broken consequence display in `get_full_context`,
removed dead code, patched docs drift) — currently uncommitted in the tree.
