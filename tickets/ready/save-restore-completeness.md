---
slug: save-restore-completeness
title: Whole-campaign saves, versioned, with rotating autosaves
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`create_save` (lib/session_manager.py:279-286) snapshots 6 of ~13 stateful
files — omitting `plots.json`, `items.json`, `threat-clocks.json`,
`campaign-memory.json`, `world-bible.json`, `ruleset.json`, `combats.json` —
so `restore_save` (:326-341) reverts part of the world and leaves quests and
clocks at present time: a world that never existed. Meanwhile
`.claude/hooks/session-autosave.sh` writes a full new snapshot every turn,
forever.

1. Snapshot and restore every stateful campaign file (enumerate from the
   campaign dir contract in docs/schema-reference.md; skip chunks/vectors/
   images and derived caches).
2. Stamp `save_version` in the snapshot; on restore, treat pre-version saves
   as partial and say so in the output rather than silently mixing state.
3. Autosaves rotate: the Stop-hook path writes `autosave` keeping at most N
   (default 3) autosave snapshots; named manual saves are untouched.
4. Update `docs/schema-reference.md:434-452` (save shape) in the same commit.

## Acceptance criteria

- [ ] Round-trip test: snapshot → mutate plots, clocks, items, NPCs, character → restore → every stateful file deep-equals the snapshot state.
- [ ] Restoring a legacy (pre-version) save prints a partial-restore warning listing what was not covered.
- [ ] After 10 autosave cycles, at most N autosave snapshots exist; named saves persist.
- [ ] `docs/schema-reference.md` save section restamped and true.

## Out of scope

Moving the memory refresh off the Stop-hook critical path (Tier 2/ideas);
save-file compression.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
