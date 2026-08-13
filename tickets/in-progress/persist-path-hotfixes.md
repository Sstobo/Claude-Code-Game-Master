---
slug: persist-path-hotfixes
title: cwd-safe gm-note/gm-time, corpse-HP guard, read-only XP status
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

Three small verified state bugs, one commit each or one combined:

1. **cwd-dependent invocation.** tools/gm-note.sh:21,24 and
   tools/gm-time.sh:14 use `$PYTHON_CMD -m lib.…`, which resolves against the
   caller's cwd — fails with `No module named 'lib'` from anywhere but repo
   root, and subagents get cwd resets. Switch to `"$LIB_DIR/<file>.py"` like
   every other wrapper; confirm the managers still import correctly as
   scripts.
2. **Corpse HP.** lib/player_manager.py:462-468 applies HP changes to dead
   characters (only the status field is guarded), so a dead PC can be healed
   to positive HP with `status: dead`. Early-return (with a clear message)
   from `modify_hp` when `status == "dead"`. Fix the false claim at
   docs/modules/player-character.md:71-72 in the same commit.
3. **Write-on-read.** `get_xp_status` (lib/player_manager.py:419) saves the
   character during a status query. Make it read-only.

## Acceptance criteria

- [ ] A test runs `gm-note.sh` and `gm-time.sh` from a non-repo cwd and both succeed.
- [ ] Test: `modify_hp(+heal)` on a dead character changes nothing and reports why; `kill` → heal → character still dead at 0 HP.
- [ ] Test: `get_xp_status` leaves the character file's mtime/content unchanged.
- [ ] `docs/modules/player-character.md` restamped with the true guard behavior.

## Out of scope

The Death Protocol flow, `_normalize_xp` kit-gating (executable-world-kit),
the broader wrapper contract work (Tier 2).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
