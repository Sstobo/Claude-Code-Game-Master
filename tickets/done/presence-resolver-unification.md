---
slug: presence-resolver-unification
title: One presence + entity resolver for scene context, consequences, and search
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: [save-restore-completeness]
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T19:53:04Z
changedFiles: [lib/entity_manager.py, lib/session_manager.py, lib/consequence_manager.py, lib/search.py, lib/scene_context.py, tests/test_presence_resolver.py, docs/modules/scene-context.md, docs/modules/entity-graph.md, docs/gotchas/npc-location-tag-split.md, docs/modules/living-world.md, docs/log.md]
resolution: one npcs_present helper; alias-aware get_npc/get_location; doors agree
reviewRounds: 1
implementer: b02c879e-1dcd-494c-a411-0de920d06868
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T20:10:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

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

- [x] Exactly one implementation of presence and one of entity resolution remain (grep-verifiable).
- [x] The doors-agree test passes for the three cases above.
- [x] An NPC resolvable by alias in `gm-npc.sh status` is also present in `gm-context.sh` output when in-scene.
- [x] Existing scene-context and consequence tests pass; claiming docs restamped.

## Out of scope

The two grounding stacks (Tier 2), NPC tag schema history (already unified),
consequence lifecycle changes.

## Verification

Lane: agent

## Blocked by

save-restore-completeness (session_manager.py one-writer chain)

---

## QA Reports

### 2026-08-14T20:10:00Z — reviewed perfect [ce3ec88d]
No correctness/regression findings. Nits: stale line citations in scene-context.md; verified.at older than generated.at; grep only scans three callers for `loc_l in locs`.

### 2026-08-14T19:58:00Z — verified [gk-t8n2wp]
One `npcs_present` (party OR exact tag); session/SceneContext/tick agree on tagged NPC + untagged party + alias; substring trap (Inn ⊄ Inner Sanctum) for presence; CLI tag-search stays substring; gm-npc.sh status + gm-context.sh wrappers pass. pytest presence_resolver + scene_context + reactivity_tick + extraction_tiering + npc_voice + get_full_context: 46 passed.

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T20:10:00Z  reviewed perfect → done  [gk-t8n2wp]
- 2026-08-14T19:58:00Z  verified → in-review, review dispatched  [gk-t8n2wp]
- 2026-08-14T19:53:04Z  claimed; doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  blocked → ready; parent trust-the-agent; blockedBy save-restore-completeness  [gk-t8n2wp]
- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
