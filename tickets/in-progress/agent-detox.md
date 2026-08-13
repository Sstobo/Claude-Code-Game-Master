---
slug: agent-detox
title: Specialist agents off the rails — efficiency directive, word quotas, mandated skeletons
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T21:30:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md) · Trust the Agent review (artifact 1a6acb14)

## Category

enhancement

## What to build

1. Delete the "EFFICIENCY DIRECTIVE… LEAST amount of steps… trust your first
   successful API call" block from all six agents that carry it
   (create-character, gear-master, monster-manual, rules-master, spell-caster,
   loot-dropper) and .claude/agents/create-character.md's copy. If latency
   matters, one line: "don't re-verify what you already have."
2. world-builder.md: delete the four word-count quotas (:62, :200-205), the
   mandated 5-part response skeleton (:148-155), and the MUST-cycle framing
   (:39); keep the tool-call persistence step and a short "what good
   expansion looks like" description.
3. npc-builder.md: 300-400-word ceiling stated three times + counting step →
   "tight, a few paragraphs, room to grow."
4. dungeon-architect.md:271-274: mandatory secret + encounter-type mix →
   "a good dungeon usually mixes encounter types and rewards curiosity."
   (:264 source-fidelity rule stays.)

## Acceptance criteria

- [ ] grep for "EFFICIENCY DIRECTIVE" and "LEAST amount of steps" returns nothing under .claude/.
- [ ] No numeric word quota remains in world-builder.md or npc-builder.md; persistence steps survive.
- [ ] create-character command's "THOROUGH selection" language no longer contradicts its agent's directives.
- [ ] dungeon-architect keeps source fidelity, loses content quotas.

## Out of scope

Kit-awareness of create-character (kit-aware-character-creation); extractor
agents (their MUST-write rules are data integrity).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
