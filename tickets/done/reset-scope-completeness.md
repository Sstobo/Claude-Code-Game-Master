---
slug: reset-scope-completeness
title: reset_world leaves plots/items/memory/bible/clocks/saves; archive copies 67M of rebuildables
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T18:54:15Z
changedFiles: [tools/gm-reset.sh, '.claude/commands/reset.md', tests/test_reset_archive.py]
resolution: reset clears the story and keeps source/world/kit; archive excludes rebuildables and fails safe
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T18:45:00Z
updatedAt: 2026-08-13T21:17:11Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

From review-bootstrap's high-effort pass (pre-existing, blessed by
reset-archive-safety's tests):

1. `reset_world` (tools/gm-reset.sh:~90) clears only npcs/locations/facts/
   consequences/overview/session-log/character.json — `plots.json`,
   `items.json`, `campaign-memory.json`, `world-bible.json`, threat clocks,
   and `saves/` survive. `/reset hard` then `/gm` still prints every STORY
   THREAD from the "deleted" campaign. Make reset clear ALL campaign state
   files (keep chunks/vectors/current-document.txt only if the reset mode
   says "keep source"; decide and document per mode). Update
   .claude/commands/reset.md's promises to match.
2. The archive copy includes `vectors/` (26M, rebuildable) and `saves/` (32M)
   — 67M per archive on conan, unbounded accumulation. Exclude rebuildables
   (vectors/) by default; consider excluding saves/ or documenting the size.
3. Extend tests/test_reset_archive.py: after reset, plots/items/memory/bible/
   clock files are gone; archive excludes vectors/.

## Acceptance criteria

- [x] After `gm-reset.sh hard --yes`, no campaign state file remains that scene context or STORY THREADS can read (test asserts plots.json etc. gone).
- [x] Archive excludes vectors/ (test asserts absence); documented what is and isn't archived.
- [x] reset.md's description matches actual clearing behavior per mode.
- [x] Full suite passes.
- [x] (review) world-bible.json + world-seed.json survive both reset modes byte-identically; reset.md lists the bible under Kept.
- [x] (review) combat_state.json cleared by both modes; gm-combat.sh reports no active fight after reset.
- [x] (review) Legacy characters/ layout leaves no readable sheets after reset (or preview stops promising it).
- [x] (review) archive exits non-zero and leaves the world untouched when the campaign dir is missing/empty.

## Out of scope

Autosave rotation (save-restore-completeness owns saves/ lifecycle).

## Verification

Lane: agent

## Blocked by

None (reset-archive-safety landed in 5afbcba).

---

## QA Reports

### 2026-08-13T21:17:11Z — pass [review-reset2-2]
reviewed: perfect (followup; all seven criteria verified serially).
Notes (non-blocking): 'World obliterated'/'Nuclear option' wording now
overstates hard mode; failed archive leaves an empty timestamped dir;
header comment lists kept dirs preview omits. Cosmetic — left as-is.

### 2026-08-13T21:14:12Z — verified (addendum) [fable-sott1]
Empty-archive test self-contained: passes in isolation, pointer stays conan,
no fixture debris; atomic os.replace sidecar helper adopted by the shared
fixture too. Orchestrator re-verified in isolation and full-file.

### 2026-08-13T20:37:14Z — verified (fix round 1) [fable-sott1]
19/19 reset tests; world-bible/world-seed in a named WORLD kept-category,
byte-identical after both modes; combat_state cleared (is_active false);
legacy characters/ cleared; empty-source archive fails before reset; rebuild
wording corrected. Implementer full suite 391 passed.

### 2026-08-13T20:28:18Z — fail [review-reset2]
reviewed: needs-changes (converges with the held whole-branch-review findings)
1. world-bible.json wrongly in STORY_FILES — it is KIT/identity, upstream of the ruleset, unrebuildable for /new-game worlds.
2. combat_state.json missing from STORY_FILES — old encounter leaks into the fresh story.
3. preview promises characters/*.json cleared; reset_world leaves the legacy dir readable.
4. nullglob lets an empty/missing source dir archive 'succeed' (rc=0) and reset proceeds — reachable via stale active-campaign.txt.
5. (minor) 'rebuilt from chunks/' is the wrong input — rebuild re-extracts from the document; archive keeps current-document.txt.

### 2026-08-13T19:10:56Z — verified [fable-sott1]
14/14 reset tests; STORY/SOURCE/KIT split driven by explicit arrays; archive
skips vectors/ at copy time with the same guarded-failure semantics; reset.md
promises match per mode. Implementer full suite 334 passed.

## History

- 2026-08-13T18:45:00Z  created → ready (from review-bootstrap findings)  [fable-sott1]
- 2026-08-13T18:54:15Z  claimed  [fable-sott1]
- 2026-08-13T19:06:36Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T19:10:56Z  verified → in-review  [fable-sott1]
- 2026-08-13T20:28:18Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T20:37:14Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T21:14:12Z  addendum verified — followup review dispatched  [fable-sott1]
- 2026-08-13T21:17:11Z  review perfect → done, committed  [fable-sott1]
