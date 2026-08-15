---
slug: trust-the-agent
title: Trust the Agent — context is state, craft is a skill, caps become disclosures
status: superseded
version: 1
supersedes: state-of-the-table
createdAt: 2026-08-14T18:52:00Z
updatedAt: 2026-08-14T20:31:00Z
---

## Problem Statement

The always-on layer (CLAUDE.md + `get_full_context`) legislates the GM:
beat arithmetic, failure NEVER-lists, exactly-3 options, fake "previously on"
from a session that never happened. Tools got more honest; the beat-hot path
got more law. The product is an LLM with helpful tools and context — not
scripts that pre-write the story.

## Solution

Context reports the world. Craft lives in `gm-craft`. Caps disclose rather
than hide. Opening seed places the PC; it does not fabricate a session.

1. Detox the always-on layer (keep player preference *flags*; drop doctrine).
2. Kit ambient in scene context; character creation follows the kit.
3. Whole-campaign saves; one presence resolver.
4. Fences become disclosures (tick, world-tick, truncations); clock ticks
   match duration; recall `--top-k`.
5. `gm.md` sheds boxes and checklists.
6. Opening seed stops writing a session that didn't happen.

## User Stories

1. As the GM, I want scene context to tell me the kit, who is here, and what
   remains truncated, so I judge — I am not told how many developments I may
   narrate.
2. As a player, I want a restore to return the whole world, and an opening
   that is a place to stand, not a cliffhanger I never earned.
3. As a player in a non-D&D world, I want death-and-rebirth to roll a
   character of *this* kit, not a 5e wizard.

## Implementation Decisions

- `get_full_context` may contain campaign, location, time, play-style flags,
  KIT block, vitals, presence + NPC memory, threads, facts, clocks, pending
  consequences with remainders, signature systems, THE WORLD REMEMBERS.
  It may not contain NEVER-lists, development caps, pre-send audits, or
  "exactly 3".
- Player preference keys (`action_menu`, `player_rolls`, `beat_length`,
  `rag_inspiration`) stay; the adaptive pacing branch reports that no
  preference is set; the opt-in `tight` branch may keep its prescription.
- `session_manager.py` is one-writer until detox, kit-block, save-restore,
  and presence have landed (encoded as `blockedBy` on those tickets).
- Opening seed: provisional location; spine/plot as visible options; no
  fake `### Session Ended` block.
- Import-pipeline tickets stay parked (`import-preflight-and-signal`).

## Testing Decisions

- Detox: context has at most one failure-stakes sentence; no NEVER-list;
  exactly-3 gone; tight branch unchanged.
- Kit block: dnd5e and conan fixtures each name kit/resolution/progression.
- Save: snapshot → mutate plots/clocks/items/NPCs/character → restore
  deep-equals; legacy saves warn; autosaves rotate.
- Presence: tagged NPC, untagged party member, alias-referenced NPC agree
  across context, consequences, and search.
- Opening: session-log after seed has no fabricated Session Ended; location
  is set; plots are not stamped active with a fake cliffhanger.
- All agent-lane.

## Out of Scope

Import extraction quality, reconciler plot awareness, extractor fan-out
caps, grounding-stack unification, `gm-roll.sh`, relative-time verbs.

## Further Notes

Sliced from the 2026-08-14 iteration plan after the inquisitor verdict on
`state-of-the-table` velocity (tools closer, always-on layer further from
the dream). `state-of-the-table` archives when save-restore, kit-block,
detox, and presence have landed.
