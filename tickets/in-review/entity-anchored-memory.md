---
slug: entity-anchored-memory
title: Facts naming an NPC attach to that NPC
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: living-world
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
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

- [ ] Logging a fact that names a known NPC results in that memory being
      retrievable under the NPC (their `events` or via scene-context cross-ref).
- [ ] When that NPC is present, the anchored memory appears in
      `gm-session.sh context` under them.
- [ ] Facts that name no known NPC still log to `facts.json` as today.
- [ ] No duplicate-storm: a fact already attached is not re-appended on repeat
      context builds.

## Out of scope

- Entity dedup (separate ticket) and the recall/vector pipeline.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
