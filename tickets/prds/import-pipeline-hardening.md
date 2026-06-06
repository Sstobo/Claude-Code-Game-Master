---
slug: import-pipeline-hardening
title: Import Pipeline Hardening — cap, reconcile, enhance, author
status: active
version: 1
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Problem Statement

First end-to-end test of `/import` (anarchists-cookbook, DCC Book 3) scored B−/78,
~75% to goal. Extraction layer strong + source-faithful (NPCs A−, Items A−, Plots
B+, Locations B). Connective tissue weak: cross-file refs don't resolve, RAG
enhancer pads thin entities with off-topic passages, per-book World Kit half never
authored. Pattern: import nails EXTRACTION, skips RECONCILIATION + AUTHORING. Plus
new requirement: imports extract EVERY entity (65 NPCs, etc.) — too many, costs
tokens + dilutes playable core.

## Solution

Harden post-extraction stages. Cap extraction to a playable top-30/type. Make
cross-file refs resolve (alias-aware runtime resolver + extract-time integrity gate
that fails on unresolved refs). Gate enhancement on relevance. Reconcile missing
locations. Author the per-book overview + campaign_rules. Polish entity correctness.

## User Stories

1. As a DM, I want imported worlds to have a tight playable cast/map (not every
   walk-on), so sessions stay focused and import is cheap.
2. As a DM, I want plot/NPC/location references to resolve when the tooling looks
   them up, so I never hit a dead link mid-session ("Princess Donut" must find
   "Donut").
3. As a DM, I want each entity's source passages to actually be about that entity,
   so enhancement helps me narrate instead of misleading me.
4. As a DM, I want the imported campaign to carry the book's signature systems
   (loot boxes, viewers, train mechanics), so play feels true to the book.

## Implementation Decisions

- **Cap = importance-ranked top-30/type.** Score = mention-frequency + main-cast /
  load-bearing priority. Main cast never dropped. Log dropped count. Applies to
  npcs/locations/items/plots.
- **Alias fix = BOTH layers.** (a) Runtime: `entity_manager` lookup strips titles
  (e.g. "Princess"), strips parentheticals, case-folds before raw `.get()`.
  (b) Extract-time: post-extraction integrity gate canonicalizes every cross-ref
  to a real key (or adds an `aliases` field) and FAILS the import if any ref
  unresolved after alias matching. Donut→Princess Donut handled here.
- Enhancer: force-include any chunk literally naming the entity/alias as seed, fill
  remaining slots only above a similarity floor (drop, don't pad), persist
  per-passage score + a name-match fraction; flag zero-name-hit entities.
- Import authors `campaign-overview.json` (name/genre/tone/in-world date) +
  `campaign_rules` block; resolves dangling `rules_doc` (write file or set null).
  Follow-on to import.md Step 6.5.
- Touch points: `lib/agent_extractor.py`, `tools/dm-extract.sh`,
  `lib/entity_manager.py`, `lib/entity_enhancer.py`, `tools/dm-enhance.sh`,
  `.claude/commands/import.md`, extractor agent prompts.

## Testing Decisions

- Agent-lane evals: cap counts ≤30 + main-cast retained; resolver resolves known
  alias set ≥92%; integrity gate fails on a planted unresolved ref; enhancer
  name-match fraction asserted; overview/campaign_rules present + rules_doc valid.
- Prior art: existing `tests/` (test_world_kit.py etc.), `dm-extract.sh validate`.

## Out of Scope

- Re-running/trimming the disposable anarchists-cookbook test campaign.
- Gameplay/combat tuning. Canvas-view feature (separate PRD).

## Further Notes

Source: workflow review wf_006c2722-f37 (anarchists-cookbook). Two related import
bugs already fixed this session (commit 9099d6c: `normalize` subcommand + Step 6.5
World Kit requirement) — campaign-overview-author is the authoring follow-on.
