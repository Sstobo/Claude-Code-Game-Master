---
slug: agent-detox
title: Specialist agents off the rails — efficiency directive, word quotas, mandated skeletons
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T21:45:08Z
changedFiles: ['.claude/agents/create-character.md', '.claude/agents/gear-master.md', '.claude/agents/monster-manual.md', '.claude/agents/rules-master.md', '.claude/agents/spell-caster.md', '.claude/agents/loot-dropper.md', '.claude/agents/world-builder.md', '.claude/agents/npc-builder.md', '.claude/agents/dungeon-architect.md', '.claude/commands/create-character.md']
resolution: specialist agents lose the efficiency directive, word quotas, and mandated skeletons; persistence stays
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T22:45:08Z
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

- [x] grep for "EFFICIENCY DIRECTIVE" and "LEAST amount of steps" returns nothing under .claude/.
- [x] No numeric word quota remains in world-builder.md or npc-builder.md; persistence steps survive.
- [x] create-character command's "THOROUGH selection" language no longer contradicts its agent's directives.
- [x] dungeon-architect keeps source fidelity, loses content quotas.

## Out of scope

Kit-awareness of create-character (kit-aware-character-creation); extractor
agents (their MUST-write rules are data integrity).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T22:45:08Z — pass [review-detox-2]
reviewed: perfect (followup; 3-line dungeon-architect fix confirmed, other
nine files unchanged). Pre-existing notes logged by round 1: create-
character step-numbering gap, save-json example missing visual_appearance
(both belong to kit-aware-character-creation), extractor word quotas
(integrity-adjacent, deliberate).

### 2026-08-13T22:00:24Z — fail [review-detox]
reviewed: needs-changes
1. dungeon-architect:273 defers to 'the source' inside the no-source branch.
2. dungeon-architect:89-98 'One secret minimum' + Room Variety mandate survive earlier in the file — quota removal half-applied.
Pre-existing notes (not this diff): create-character Step-2 numbering gap; save-json example omits visual_appearance; extractor word quotas (out of scope).

### 2026-08-13T21:58:08Z — verified [fable-sott1]
Greps clean: no EFFICIENCY DIRECTIVE, no word quotas, no mandatory secret;
persistence steps intact (world-builder Step 4 + npc-builder tools); no doc
owners for any of the ten files. Implementer suite 409 passed (transient
reset-archive collisions attributed to concurrent runs, passed serially).

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-13T21:45:08Z  claimed  [fable-sott1]
- 2026-08-13T21:58:08Z  verified → in-review  [fable-sott1]
- 2026-08-13T22:00:24Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T22:45:08Z  review perfect → done, committed  [fable-sott1]
