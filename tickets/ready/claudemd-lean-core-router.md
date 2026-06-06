---
slug: claudemd-lean-core-router
title: Reduce CLAUDE.md to a lean ~150-line core + router (craft wisdom last)
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [claudemd-extract-tables]
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

Final step of the split — high blast radius, needs human sign-off. Reduce
CLAUDE.md to ~150 lines: the core loop, persist-before-narrate, the action
router (names which skill to load per action), and pointers. Move the "Art of
Dungeon Mastering" CRAFT WISDOM into a skill loaded for narration — it is the
product's soul, so it moves LAST and most carefully. The RULES SYSTEM itself is
the World Kit's skill (a Dune import ships its own combat/progression skill, not
5e).

## Acceptance criteria

- [ ] CLAUDE.md is ~150 lines: core loop, persist-before-narrate, action router, pointers.
- [ ] Craft wisdom lives in a narration skill, loaded when narrating; content preserved verbatim (PROTECT).
- [ ] Router reliably names the skill to load per action type; fallback path documented if a skill fails to load.
- [ ] Human review confirms no soul/voice/craft regression across a full play beat (combat, social, exploration).
- [ ] Per-turn context cost measurably reduced vs the 1196-line baseline (observability note).

## Verification

Lane: manual

## Blocked by

claudemd-extract-tables

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
