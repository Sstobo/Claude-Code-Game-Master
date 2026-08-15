---
slug: entity-anchored-memory
title: Facts naming an NPC attach to that NPC
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: living-world
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T15:54:00Z
changedFiles: [lib/session_manager.py, docs/modules/scene-context.md, tests/test_entity_anchored_memory.py]
resolution: surface facts naming a present NPC under that NPC at read time (full key + aliases, word-boundary), so per-NPC memory is not lost to the global facts log
reviewRounds: 2
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:04:00Z
---

## Parent

Living World (prds/living-world.md)

## Category

enhancement

## What to build

The wench's "she knows more" tell was logged to `facts.json` and never reached
her NPC record, so the world can't recall it under her when she's next on stage.
Close the gap between the global facts log and per-NPC memory.

- When a fact/note references a known NPC name, also append it to that NPC's
  `events` (the field scene context already surfaces), OR have scene context
  cross-reference facts by present-NPC name.
- Prefer extending the existing `gm-note.sh` / `gm-npc.sh update` / scene-context
  path over introducing a new store.

## Acceptance criteria

- [x] Logging a fact that names a known NPC results in that memory being
      retrievable under the NPC (their `events` or via scene-context cross-ref).
- [x] When that NPC is present, the anchored memory appears in
      `gm-session.sh context` under them.
- [x] Facts that name no known NPC still log to `facts.json` as today.
- [x] No duplicate-storm: a fact already attached is not re-appended on repeat
      context builds.
- [x] (review) A present NPC whose name is multi-token with a common-word first
      token (e.g. "Old Man Withers", "Red Sonja") must NOT get an unrelated fact
      attached when the fact merely uses the common word in lowercase ("the old
      rope frayed", "the red door creaked"); only the full key, an alias, or a
      genuine proper-name token attaches.

## Out of scope

- Entity dedup (separate ticket) and the recall/vector pipeline.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-15T16:04:00Z — pass [reviewer]
reviewed: perfect (followup) — false-positive class gone (needles = full key + aliases only, `\b...\b` IGNORECASE); Old-Man-Withers/Red-Sonja/Ana-Banana guards pass; full-key + alias attachment intact; read-only, present-non-party gating, de-dup vs already_shown + events, cap + remainder all hold; doc clause matches code and stamp reflects the body change.
Notes: (non-blocking) `test_alias_path_attaches` uses an alias phrase that also contains the bare key, so it doesn't isolate the alias-only needle — path correct by inspection.

### 2026-08-15T16:02:00Z — fix verified, followup review dispatched [ss-rt14b]
- Dropped the auto leading-proper-name-token needle from `_npc_anchored_facts`; now matches only the full NPC key + explicit `aliases` on a word boundary (IGNORECASE safe for full names). scene-context.md clause corrected + restamped.
- 7 anchored tests pass, incl. 3 new: common-leading-token false-positive guard (Old Man Withers / Red Sonja not matched by "the old rope"/"the red door"), full-multiword-key still attaches, alias path attaches. Only the pre-existing action-menu test fails (unrelated).

### 2026-08-15T16:01:00Z — fail [reviewer]
reviewed: needs-changes
- session_manager.py:1257-1262 — the auto-derived leading-proper-name-token needle + `re.IGNORECASE` is a false-positive path. For a multi-token NPC whose first token is a common word, `\b<lead>\b` matches ordinary lowercase prose: "Old Man Withers"←"the old rope frayed", "Red Sonja"←"The red door creaked", "Young Tom"←"a young sapling", "Black Hand"←"the black parchment", "Princess Donut"←"the princess of a distant realm" (5/6 realistic names wrongly matched). The `{the,a,an}` stopword set is far too narrow, and IGNORECASE fires on everyday lowercase usage. Untested — both fixture NPCs are single-token so the leading-token path never runs.
Fix direction: drop the auto leading-token needle; attach only on the full NPC key and explicit `aliases` (word-boundary). Full multi-word keys / real aliases are specific enough that IGNORECASE is safe; the single common-word token was the whole problem. Short-name matching is what `aliases` (now recorded by entity-dedupe) are for.

### 2026-08-15T15:58:30Z — verified [ss-rt14b]
- Read-time `_npc_anchored_facts` helper: flattens facts.json, word-boundary-matches the present NPC's key + aliases + leading proper-name token, excludes `already_shown` (PREVIOUSLY ON / world-remembers) and the NPC's own `events`; renders `remembers: <fact>` under non-party present NPCs, capped at 3 with `_remainder` disclosure. Read-only, no write coupling → no duplicate-storm.
- 4 new tests pass (fact-names-present-NPC surfaces under them; fact naming nobody present is not attached; word-boundary guard "Ana"≠"Banana"; no double-render when fact already in events). Rest of `test_get_full_context` green.
- [pre-existing, out of scope] `test_action_menu_on_is_a_few_numbered_not_exactly_three` fails on HEAD independent of this change (implementer confirmed via stash) — the committed action-menu text says "exactly THREE" while the stale test expects "a few numbered".

## History

- 2026-08-15T16:04:00Z  followup review perfect → done + committed  [ss-rt14b]
- 2026-08-15T16:02:00Z  fix verified (7 tests) → followup review dispatched  [ss-rt14b]
- 2026-08-15T16:01:00Z  review needs-changes (leading-token false positives) → re-delegating fix; reviewRounds 2  [ss-rt14b]
- 2026-08-15T15:58:30Z  verified → in-review  [ss-rt14b]
- 2026-08-15T15:55:30Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T15:54:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
