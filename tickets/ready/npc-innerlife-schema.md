---
slug: npc-innerlife-schema
title: NPC inner-life fields (goal/secret/mood/voice/bonds) + populate
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [npc-voice-surfacing]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Give the "every NPC has an agenda" craft demand somewhere to live. Additively
extend the NPC model with `goal`, `secret`, `current_mood` (shifts on
interaction + persists), `voice` (canonical lines/descriptor — integrates with
`npc-voice-surfacing`), and `bonds` (+/- relationship values to PC/other NPCs).
Defaults so old campaigns load. Populate from `/enhance` + npc-builder. Surface
goal + mood + secret-EXISTENCE (not the secret text) + voice for present NPCs.
WATCH MEMORY.md: add fields additively; never reuse the extraction schema for
runtime.

## Acceptance criteria

- [ ] NPC schema additively gains `goal`, `secret`, `current_mood`, `voice`, `bonds` with safe defaults.
- [ ] Existing DCC `npcs.json` loads unchanged (round-trip test); missing fields default, not crash.
- [ ] `/enhance` + npc-builder populate the new fields from source material.
- [ ] `current_mood` shifts on a recorded interaction and persists across sessions.
- [ ] `get_full_context` surfaces goal + mood + secret-existence + voice for present NPCs (NOT secret text).
- [ ] Runtime schema kept separate from extraction schema (no field bleed per MEMORY.md).

## Verification

Lane: agent

## Blocked by

npc-voice-surfacing

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
