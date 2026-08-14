---
slug: character-save-kit-vitals
title: save_character.py persistence layer must honor the World Kit (attributes, authored HP, kit vitals)
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T18:09:55Z
changedFiles: [features/character-creation/save_character.py, lib/player_manager.py, lib/world_kit.py, tools/gm-player.sh, docs/modules/player-character.md, tests/test_kit_vitals.py]
reviewRounds: 2
resolution: kit-honoring save path + first-class vitals
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T18:51:32Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

CLAUDE.md states the World Kit is the rules authority ("The world's rules come
from its World Kit, not from D&D 5e"). The character save path ignores it.

Observed creating Conan in a Hyborian-kit campaign:

1. **Key mismatch.** `features/character-creation/save_character.py:86` requires
   `stats`; the kit's `stat_schema` calls them `attributes`. Failure message is
   `Missing required field: stats` with no hint. Two wasted round-trips.
2. **HP silently overridden.** An authored 58 max HP was recalculated to 51 by
   a 5e CON-modifier formula (save_character.py:95).
3. **5e saves on a non-5e class.** `calculate_saves(class_name, ...)` ran
   against class "Reaver", which has no 5e meaning.
4. **Kit vitals are second-class.** `ruleset.json` declared vitals
   `["hp","vigor","corruption"]`; only `hp` is a real tracked stat. `vigor` and
   `corruption` survive only as passenger JSON with no manager support, so the
   kit's own signature systems cannot be persisted or displayed.

Make the character path kit-driven: read `stat_schema.attributes` for the
attribute key set (accepting `stats` as a legacy alias), do not recompute
authored vitals unless the kit's progression model asks for it, skip 5e save
derivation for non-dnd5e kits, and give every vital in `stat_schema.vitals` the
same first-class read/write support `hp` has.

## Acceptance criteria

- [x] Saving a character with `attributes` succeeds in a non-dnd5e kit campaign; `stats` still accepted.
- [x] An authored max HP is preserved exactly; no silent recalculation outside dnd5e.
- [x] No 5e saving-throw derivation runs for a kit whose name is not dnd5e.
- [x] `vigor` and `corruption` (or any kit-declared vital) can be read and modified via gm-player.sh and appear in `gm-player.sh show`.
- [x] A test creates a character under the Hyborian kit fixture and asserts all four behaviors.
- [x] (review) vital on a legacy characters/<id>.json campaign resolves the active PC and saves without raising.
- [x] (review) vital hp --json returns the same vital/current/max keys as other vitals (or the divergence is documented at the verb).
- [x] (review) gm-player.sh help names the first positional as the vital, not the character.
- [x] (review) A dnd5e save with explicit hp preserves it verbatim (pins the intentional change).

## Out of scope

The interactive create-character wizard flow — that is kit-aware-character-creation.
Rendering vitals in scene context, and the level-up path. Do not change dnd5e
campaign behavior.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T18:51:32Z — pass [review-vitals-2]
reviewed: perfect (followup). Non-blocking notes carried to
kit-aware-character-creation: silent 10/10 fallback for non-5e saves with no
authored hp should surface a warning; create-character template lacks an hp
key. Also noted: conan's live ruleset.json has no `kit` field (reads as
'custom') — legacy-kit stamping to consider under import-bible-kit-wiring.

### 2026-08-13T18:48:13Z — verified (fix round 1) [fable-sott1]
13/13 kit-vitals tests; legacy-layout crash reproduced-then-fixed by the
implementer; unified response shape; help text names the vital. Deliberate
non-stamp of game-core-and-world-kit.md (its :84 citation is stale — deferred
to the T3 symbol-citation docs ticket) and schema-reference.md (five of six
sources mid-edit by other tickets). Implementer full suite 330 passed.

### 2026-08-13T18:44:57Z — fail [review-vitals]
reviewed: needs-changes
1. player_manager.py:580 — _save_character(name=None) on legacy characters/<id>.json layout → AttributeError (reproduced); save with resolved char_name.
2. :568 — vital hp --json data shape polymorphic (three shapes across read/write/delegate).
3. gm-player.sh:197 + player-character.md:36 — help reads vital <name> like sibling verbs where <name>=character; steers 'vital Conan -2'.
4. save_character.py:80 — authored hp now preserved on dnd5e too (better behavior, but unpinned under a "dnd5e unchanged" criterion).
Nits: player-character.md points at game-core doc for the vitals declaration (actually schema-reference:482); world_kit.py claiming docs want restamp --verify.

### 2026-08-13T18:39:59Z — verified [fable-sott1]
10/10 kit-vitals tests; live: gm-player.sh vital corruption reads on conan,
undeclared vital refused with the declared list. Implementer full suite 313
passed. Judgment call accepted: non-dnd5e kit with no authored HP gets neutral
10/10, never the 5e formula (matches "no recalculation outside dnd5e").
player-character.md restamped; corpse-HP claim untouched per scope.

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-13T18:09:55Z  claimed  [fable-sott1]
- 2026-08-13T18:39:59Z  verified → in-review  [fable-sott1]
- 2026-08-13T18:44:57Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T18:48:13Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T18:51:32Z  review perfect → done, committed  [fable-sott1]
