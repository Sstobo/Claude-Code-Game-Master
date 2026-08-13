---
slug: skill-guidance-pass
title: gm-skills / gm-social / gm-craft — law becomes craft guidance
category: enhancement
kind: afk
priority: p1
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

Three skill files state good instincts as law. Rewrite as guidance the GM
weighs against the fiction — same wisdom, no bans:

1. **gm-skills/SKILL.md:40 + gm-social/SKILL.md:33 "no retry" ban** — drop
   the banned-phrase list ("give me a reason", "convince me" can be real
   escalation). Keep: "a failed check costs something and the goal is denied;
   don't hand the stake back for free."
2. **gm-social/SKILL.md:34** — "acts on the refusal, including violence"
   pre-decides the NPC's move; soften to "the refusal has consequences the
   NPC chooses from their goals."
3. **gm-skills/SKILL.md:24,42-47 failure matrix** — the nine-cell
   margin-to-outcome grid with 5e damage dice (in a kit-agnostic system)
   shrinks to three severity ideas (near-miss / clear failure / disaster)
   with no per-band dice; "no band is free" survives as the one-line stake
   principle.
4. **gm-craft/SKILL.md:34-36** — the stop-and-rewrite pre-send ritual becomes
   craft ("a world with a voice should never sound interchangeable"),
   matching the file's own "wisdom, not rules" framing.

## Acceptance criteria

- [ ] No banned-phrase list, no prescribed-outcome sentence, no per-band dice table remains in the three files (grep for "Never end a failure", "including violence", "1d4").
- [ ] The stake principle (failure costs; goal denied) survives in both mechanics skills.
- [ ] gm-craft contains no process gate; its voice guidance survives.
- [ ] tests/test_lean_core.py (asserts on skill content, if any) updated; full suite passes.

## Out of scope

CLAUDE.md and injected context (core-prompt-detox); the D&D-kit skills
(combat/levelup/spellcasting — content is kit-legitimate); routing.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
