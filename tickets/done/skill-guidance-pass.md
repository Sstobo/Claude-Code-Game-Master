---
slug: skill-guidance-pass
title: gm-skills / gm-social / gm-craft — law becomes craft guidance
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T21:31:28Z
changedFiles: ['.claude/skills/gm-skills/SKILL.md', '.claude/skills/gm-social/SKILL.md', '.claude/skills/gm-craft/SKILL.md']
resolution: failure doctrine adopted and softened — stake principle stays, bans and pre-made judgments go
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T21:44:47Z
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

- [x] No banned-phrase list, no prescribed-outcome sentence, no per-band dice table remains in the three files (grep for "Never end a failure", "including violence", "1d4").
- [x] The stake principle (failure costs; goal denied) survives in both mechanics skills.
- [x] gm-craft contains no process gate; its voice guidance survives.
- [x] tests/test_lean_core.py (asserts on skill content, if any) updated; full suite passes.
- [x] (review) The fail-forward example no longer grants the stated goal on a failure.
- [x] (review) Information bands 3-5 and 6-9 have distinct outcomes.

## Out of scope

CLAUDE.md and injected context (core-prompt-detox); the D&D-kit skills
(combat/levelup/spellcasting — content is kit-legitimate); routing.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T21:44:47Z — pass [review-skills-2]
reviewed: perfect (followup). Nits recorded: Information ladder not strictly
monotonic (1-2 can bite harder than 3-5); gm-craft's declarative closer
carries less imperative force — both deliberate trades toward guidance-
not-law. Commit includes the adopted GM-session base edits (user-authorized).

### 2026-08-13T21:43:12Z — verified (fix round 1) [fable-sott1]
Fail-forward example now denies the goal; Information bands distinct at
3-5/6-9/10+; third restatement removed. Implementer suite 399 passed.

### 2026-08-13T21:42:28Z — fail [review-skills]
reviewed: needs-changes
1. gm-skills:32 fail-forward example grants the goal on a failure — contradicts the doctrine six lines below.
2. gm-skills:47 Information bands 3-5 and 6-9 describe the same outcome.
Nit: re-attempt rule stated three times (gm-social:37 redundant).

### 2026-08-13T21:40:48Z — verified [fable-sott1]
Adopt+soften applied per user decision: stake doctrine, cost-before-roll,
materially-changed re-attempt rule, and all persistence instructions
survive; banned phrases, prescribed violence, 5e dice, and the gm-craft
pre-send ritual are gone (grep-verified). Commit will include the adopted
base edits from the user's GM session (authorized). Full suite 399 passed.

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-13T21:31:28Z  claimed  [fable-sott1]
- 2026-08-13T21:31:56Z  blocked: file collision — another session is actively authoring the no-retry doctrine these files would soften  [fable-sott1]
- 2026-08-13T21:37:30Z  unblocked: user chose adopt+soften — this ticket now owns the other session's doctrine edits  [fable-sott1]
- 2026-08-13T21:40:48Z  verified → in-review  [fable-sott1]
- 2026-08-13T21:42:28Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T21:43:12Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T21:44:47Z  review perfect → done, committed  [fable-sott1]
