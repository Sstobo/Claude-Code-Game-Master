---
slug: gm-md-slim
title: gm.md sheds its templates, checklists, and pre-rolled stories
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: trust-the-agent
blockedBy: [core-prompt-detox]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-14T18:52:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

## Category

enhancement

## What to build

1. **ASCII templates** (~150 lines across gm.md:51-74, 98-117, 281-294,
   349-431): replace each box-drawing template with a one-line description of
   what the display must convey. Also honors phone play (no fenced boxes —
   standing user preference).
2. **Startup checklist** (gm.md:182-231): Steps 1-2 (context load + location
   reconcile) stay required; Step 4's "Build Mental Model" checkboxes deleted;
   Step 3 softened to "pull full NPC detail when the summary isn't enough."
3. **One-shot mode** (gm.md:136-175): the d6 scenario table, "3-5 encounters
   maximum", and "skip extensive backstory/world-building" become "one-shots
   start fast and stay tight; pick a hook that fits the player's appetite."
4. **create-character command** (:288): ASCII-art/emoji-decoration mandate →
   "present the finished sheet clearly, phone-friendly."

Coordinate with core-prompt-detox (blocker): that ticket removes the
death-menu duplication from gm.md; this one does the rest.

## Acceptance criteria

- [ ] No box-drawing template blocks remain in gm.md (grep for ╔/┌/═ fences); each replaced by a content description.
- [ ] Startup section: two required state steps, no self-interrogation checklist.
- [ ] No d6 scenario table, encounter cap, or skip-setup mandate in one-shot mode.
- [ ] create-character presents sheets without an ASCII-art mandate.
- [ ] Full suite passes (test_lean_core assertions updated if they pin gm.md content).

## Out of scope

CLAUDE.md (core-prompt-detox); /help accuracy (T3.3); kit-aware creation flow.

## Verification

Lane: agent

## Blocked by

core-prompt-detox

---

## QA Reports

## History

- 2026-08-14T18:52:00Z  parent → trust-the-agent  [gk-t8n2wp]
- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
