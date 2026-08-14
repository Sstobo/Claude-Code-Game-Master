---
slug: npc-memory-in-scene
title: Present NPCs carry what they remember into the scene brief
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: make-the-world-remember
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: Presence no longer requires canonical dialogue; present NPCs render their recent events via a renderer shared with the party block. CLAUDE.md gained the missing persistence row. Landed inside commit 2f36249 (a concurrent session committed the working tree).
reviewRounds: null
implementer: claude-fable-5
createdAt: 2026-08-14T02:25:26Z
updatedAt: 2026-08-14T02:25:26Z
---

## Parent

Make the World Remember (prds/make-the-world-remember.md)

## Category

bug

## What to build

Two defects in the same block keep per-NPC memory out of every scene.

1. **Voice-less NPCs vanish.** `_present_npc_voices` (`lib/session_manager.py:829-854`)
   computes presence correctly, then discards the NPC if `context` is empty:
   `if not vlines: continue` (`:851`). An NPC standing in the room with a mood, a goal and
   a secret is absent from the brief because a RAG pass never gave them a quotable line.
   This hits stubbed NPCs (`lib/minor_stubs.py`) and every original `/new-game` world.

2. **Their history is never rendered.** `gm-npc.sh update "<name>" "<event>"` writes to
   `npcs.json[name].events` (`lib/npc_manager.py:88-112`) and the session brief renders it
   **only for party members** (`lib/session_manager.py:635-645`). The NPC VOICES block
   (`:654-669`) prints mood/goal/"has a secret" and never touches `events`. The shopkeeper
   you betrayed keeps a perfect log that nothing reads.

Work:

1. Drop the `:851` early-out so presence no longer requires voice lines. An NPC with no
   lines still appears, with whatever they have.
2. Rename the helper and the block heading from "voices" to present-NPC framing, since the
   block now carries more than dialogue. Keep the read-only contract on `context` intact
   (never mutate it — PROTECT canonical-voice extraction).
3. Render each present NPC's recent `events` in their entry. Factor the party block's
   existing loop (`:635-645`) into one small helper used by both sites rather than
   duplicating it — same format (`Recent: "..." -> "..."`), same `self._truncate` at 120
   chars, same 2-normally / 3-with-`--full` bound.

## Acceptance criteria

- A campaign whose NPC is tagged to the current location and has an empty `context` shows
  that NPC in `gm-session.sh context`.
- That NPC's most recent `events` text appears in the brief.
- Party-member event rendering is unchanged in format and bounds (one renderer, same output).
- `context`/voice lines are still never mutated by a context read.
- `docs/modules/scene-context.md` (claims `lib/session_manager.py`) updated and restamped in
  the same commit; its "NPC secrets are surfaced by existence only" note must stay true.

## Notes

`presence-resolver-unification` (in `ready/`) rewrites the presence *rule* across three call
sites including this function. These two touch the same code; whichever lands second should
rebase onto the other rather than reverting it. This ticket deliberately does not change who
counts as present — only what is shown for them.
