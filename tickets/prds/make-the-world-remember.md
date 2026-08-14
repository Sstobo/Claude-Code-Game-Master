---
slug: make-the-world-remember
title: Make the World Remember — wire the push side of memory and pressure
status: archived
version: 1
supersedes: null
createdAt: 2026-08-14T02:25:26Z
updatedAt: 2026-08-14T17:27:15Z
---

## Problem Statement

The magic of a table GM is not the rules, it is that they *remember*: the paladin lied
to the innkeeper in session 3, and in session 11 the innkeeper's brother refuses him a
room. Two audits (memory path, living-world path; 2026-08-14) found that this harness
already **stores** everything needed for that and **reads almost none of it**. The
machinery is built and well-factored; the push side is missing.

- `CampaignMemory.recall()` and `memoir()` have zero automated callers
  (`lib/campaign_memory.py:132,207`). Embeddings, cosine search, arc entries and
  `open_debts` are all built and all unread. Recall fires only if the GM model chooses
  to ask — which requires already suspecting there is something to remember, the exact
  failure memory exists to fix.
- The NPC VOICES block prints mood, goal and "has a secret" but never an NPC's `events`
  (`lib/session_manager.py:654-669`). Per-NPC history is written by `gm-npc.sh update`
  and rendered **only for party members** (`:635-645`).
- An NPC with no canonical voice lines is dropped from the scene brief entirely
  (`lib/session_manager.py:851`), so stubbed and original-world NPCs are invisible while
  standing in the room.
- `gm-note.sh:11` advertises `player_choices` and `npc_relations` categories that
  `_key_facts` never reads (`lib/session_manager.py:818`). Those writes go into a hole.
- A threat clock stores a `consequence` string (`lib/threat_clocks.py:33-35`) that is only
  echoed in the FULL line, never written into the consequence engine. A filled clock is a
  passive line, not a beat that arrives.

## Solution

Four surgical changes, all in the push direction. No new subsystem and no new entity
type — each one wires up storage that already exists, so the diff is small and the payoff
is that the world starts volunteering its own memory.

## User Stories

1. As a player, I want an NPC I wronged to act like they remember it, without the GM being
   asked to look it up.
2. As a player, I want a promise made in session 3 to resurface in session 11 unprompted.
3. As a player, I want the choices I made recorded in `player_choices` to still matter later.
4. As a player, I want a threat clock that fills to actually go off.

## Implementation Decisions

- Presence in the scene brief no longer requires canonical voice lines; the block carries
  each present NPC's recent `events`, using one shared renderer with the party block.
- `get_full_context` gains a "THE WORLD REMEMBERS" block seeded from live scene state
  (current location + present NPC names) plus `open_debts` from the latest arc entry.
  It degrades to empty on any failure, matching `SceneContext.build`'s RAG pattern.
- `_key_facts` reads `player_choices` and `npc_relations` alongside the three `plot_*`
  categories.
- A clock that reaches full writes its stored `consequence` into the consequence engine
  once, guarded by a flag so ticks do not duplicate it. `gm-clock.sh add` gains the
  `--consequence` flag it was missing, so hand-made clocks can carry one.

## Testing Decisions

- One test per change, in the existing suite's style (fixture campaign dir, no framework
  beyond pytest): NPC memory surfaces for a voice-less tagged NPC; a stored `open_debts`
  item reaches context with no explicit recall call, and a broken memory file still builds;
  a `player_choices` note reaches context; a filled clock writes exactly one consequence
  and ticking again writes none.
- All agent-lane; no manual QA required.

## Out of Scope

Stakes/cost enforcement in code — "what did that failure cost" is a judgment call that
belongs in doctrine, and a checker would fight `core-prompt-detox`. Recall `--top-k` on the
CLI and tick disclosure are already owned by `advisory-fences`. Presence-rule unification
across the three call sites is owned by `presence-resolver-unification`.

## Further Notes

OKF: `docs/modules/scene-context.md` claims `lib/session_manager.py`;
`docs/modules/living-world.md` claims `lib/threat_clocks.py`;
`docs/modules/campaign-memory.md` covers the recall path. Update and restamp claiming docs
in the same commit as the code.

---

## History

- 2026-08-14T02:25:26Z  created, status active  [fable-remember]
- 2026-08-14T12:30:00Z  all four tickets shipped  [fable-remember]
- 2026-08-14T17:27:15Z  archived — four tickets in done/  [gk-a8r14q]
