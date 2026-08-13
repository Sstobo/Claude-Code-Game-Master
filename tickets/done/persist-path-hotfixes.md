---
slug: persist-path-hotfixes
title: cwd-safe gm-note/gm-time, corpse-HP guard, read-only XP status
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T18:54:15Z
changedFiles: [tools/gm-note.sh, tools/gm-time.sh, lib/note_manager.py, lib/time_manager.py, lib/player_manager.py, docs/modules/player-character.md, tests/test_persist_path_hotfixes.py]
resolution: cwd-safe note/time wrappers, corpse-HP frozen, read-only XP status
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T21:12:35Z
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

- [x] A test runs `gm-note.sh` and `gm-time.sh` from a non-repo cwd and both succeed.
- [x] Test: `modify_hp(+heal)` on a dead character changes nothing and reports why; `kill` → heal → character still dead at 0 HP.
- [x] Test: `get_xp_status` leaves the character file's mtime/content unchanged.
- [x] `docs/modules/player-character.md` restamped with the true guard behavior.

## Out of scope

The Death Protocol flow, `_normalize_xp` kit-gating (executable-world-kit),
the broader wrapper contract work (Tier 2).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T21:12:35Z — pass [review-persist]
reviewed: perfect. Non-blocking notes: 'Revive' wording reworded by
orchestrator pre-commit to point at the Death Protocol (no revive verb
exists); onboarding-and-death.md verify-restamp DEFERRED to the T3
symbol-citation pass (its become() line refs pre-date this ticket and are
already off; content not falsified); award_xp/spectacle/non-hp vitals still
move on a dead PC — documented asymmetry, HP only is frozen; fixture
live-state pattern tracked in test-fixture-isolation.

### 2026-08-13T20:38:49Z — verified [fable-sott1]
Implementer completed but never reported; orchestrator verified directly
from the tree: 8/8 new tests pass; gm-note.sh runs from /tmp; modify_hp
refuses on status==dead (guard at top, kill_character does not route
through it); get_xp_status contains no save call; player-character.md
corpse claim updated + restamped 20:38:05Z. Late implementer report confirms:
lib/note_manager.py + lib/time_manager.py received the permitted script shim
(+ usage-string fixes); cd "$PROJECT_ROOT" added because world-state resolves
against caller cwd — root cause filed as wrapper-cwd-anchoring ticket.

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-13T18:54:15Z  claimed  [fable-sott1]
- 2026-08-13T19:06:36Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T20:38:49Z  verified → in-review  [fable-sott1]
- 2026-08-13T21:12:35Z  review perfect → done, committed  [fable-sott1]
