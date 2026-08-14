---
slug: presence-resolver-unification
title: One presence + entity resolver for scene context, consequences, and search
category: bug
kind: afk
priority: p1
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
updatedAt: 2026-08-14T17:56:17Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

"Who is in this scene" has three implementations that disagree:
lib/session_manager.py:792-793 (party OR exact tag match),
lib/consequence_manager.py:266-273 (same rule, reimplemented), and
lib/search.py:90 (substring match — the one SceneContext.build uses via :45).
A party member with no location tag is present to the consequence engine and
absent from the place brief; docs/modules/scene-context.md:73-75 asserts the
doors agree. Entity resolution also splits: EntityManager._get_entity
(lib/entity_manager.py:132-142) is alias-aware; WorldSearcher.get_npc/
get_location (lib/search.py:228-236) are exact-match.

1. One module (e.g. `lib/world_view.py` or folded into entity_manager):
   `npcs_present(location)` (party-always-present + tag match; decide
   substring-vs-exact deliberately and document why) and
   `resolve_entity(name)` (alias-aware).
2. Switch all three presence callers and the search getters onto it.
3. A test asserting both context doors and the consequence tick agree on
   presence for: tagged NPC, untagged party member, alias-referenced NPC.
4. Correct docs/modules/scene-context.md (and living-world.md if its account
   moves) in the same commit.

## Acceptance criteria

- [ ] Exactly one implementation of presence and one of entity resolution remain (grep-verifiable).
- [ ] The doors-agree test passes for the three cases above.
- [ ] An NPC resolvable by alias in `gm-npc.sh status` is also present in `gm-context.sh` output when in-scene.
- [ ] Existing scene-context and consequence tests pass; claiming docs restamped.

## Out of scope

The two grounding stacks (Tier 2), NPC tag schema history (already unified),
consequence lifecycle changes.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
