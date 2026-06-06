---
slug: npc-voice-surfacing
title: Surface canonical NPC voice at the speaking moment
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [story-spine-context]
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

Turn the most magical unused asset into immersion. The NPC `context` field
already stores verbatim book dialogue (e.g. Mordecai's actual lines) but is
loaded by nothing during play. Surface present-NPC voice lines in
`get_full_context`, plus a `dm-npc.sh voice <name>` the DM calls right before an
NPC speaks. PROTECT the canonical-voice extraction — read it, never overwrite it.

## Acceptance criteria

- [ ] `dm-npc.sh voice <name>` returns the NPC's canonical voice lines / descriptor (structured JSON per the wrappers ticket if landed, else plain).
- [ ] `get_full_context` includes voice snippets for NPCs at the current location.
- [ ] No mutation of the existing NPC `context` field.
- [ ] Graceful when an NPC has no voice data (empty, no error).
- [ ] Test: DCC fixture surfaces a known Mordecai/Donut line when that NPC is present.

## Verification

Lane: agent

## Blocked by

story-spine-context

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
