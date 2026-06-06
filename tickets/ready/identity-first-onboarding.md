---
slug: identity-first-onboarding
title: Identity-first onboarding ("Who are you in this world?")
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [open-character-schema, single-front-door]
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

Replace the mandatory 9-step 5e builder with one question: "Who are you in this
world?" → play a canon character (lift stats/voice from `npcs.json`), an original
(name + one-line concept, infer stats silently against the active kit), or a
nameless traveler (zero mechanics). Mechanics get inferred + persisted invisibly
against the kit's stat schema; the full builder stays opt-in. Delivers half the
"fast magic" — a prompt-flow change with no concurrency risk. Needs feel review →
hitl.

## Acceptance criteria

- [ ] Onboarding opens with the single "Who are you in this world?" choice (canon / original / nameless).
- [ ] Canon path lifts an NPC's stats + voice from `npcs.json` into the player character.
- [ ] Original path takes name + one-line concept and infers attributes silently against the active kit schema.
- [ ] Nameless path starts play with zero required mechanics.
- [ ] Full builder remains available as opt-in.
- [ ] Human review confirms time-to-first-scene drops dramatically vs the 9-step flow.

## Verification

Lane: manual

## Blocked by

open-character-schema, single-front-door

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
