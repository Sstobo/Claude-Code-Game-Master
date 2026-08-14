---
slug: core-prompt-detox
title: The always-on layer stops bossing — beat mandate, failure doctrine, format mandates
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
updatedAt: 2026-08-14T17:56:17Z
---

## Parent

State of the Table (prds/state-of-the-table.md) · Trust the Agent review (artifact 1a6acb14)

## Category

enhancement

## What to build

Vision: clear prompting + tools that help, no process guardrails. The always-on
layer (CLAUDE.md + `get_full_context`-injected prose) currently pre-makes
creative judgments on every beat:

1. **CLAUDE.md:115 beat-shape mandate** — "AT MOST ONE new world development…
   Test before sending: could the player say 'wait — I do X'? If yes, cut
   there." Keep the true core (don't fast-forward past player agency; one
   clear beat at a time); DELETE the one-development arithmetic and the
   pre-send audit ritual.
2. **session_manager.py:460-472 failure doctrine** — ~130 words of always-
   injected adjudication law ("NEVER convert a failure into a retry, a hint…
   a failure that costs nothing is a bug"). Cut to one informing sentence
   ("failure should cost something; decide the stake before the roll").
3. **session_manager.py:443-447 adaptive pacing cap** — the no-preference
   branch injects "at most one new world development"; its job is to report
   that no preference is set, not to set one. Drop the cap from the adaptive
   branch (the opt-in "tight" branch keeps its prescription — that's a player
   preference).
4. **CLAUDE.md format mandates** — "exactly 3 numbered options" → "a few
   numbered options"; the Death Protocol keeps its three routes but drops the
   verbatim menu script ("offer these three routes in whatever framing the
   moment calls for"); gm.md points at CLAUDE.md instead of duplicating.

COLLISION WARNING: lib/session_manager.py carries another session's
uncommitted preference-feature hunks (player_rolls/beat_length/
rag_inspiration). Claim this ticket ONLY when that file is clean or by
explicit user instruction to work around them; the edits here touch the same
region.

## Acceptance criteria

- [ ] CLAUDE.md contains no numeric cap on world developments per beat and no pre-send self-audit instruction; player-agency guidance survives.
- [ ] `gm-session.sh context` output contains at most one sentence about failure stakes, and no NEVER-list.
- [ ] The adaptive pacing line sets no numeric cap; the "tight" preference branch is unchanged.
- [ ] Exactly-3 relaxed everywhere it appears (grep); death hand-off keeps three routes, loses the script; no duplicate menu text between CLAUDE.md and gm.md.
- [ ] tests/test_lean_core.py + test_get_full_context updated and passing; full suite passes.
- [ ] docs claiming these sources (play-turn.md, scene-context.md) restamped where claims move.

## Out of scope

gm.md's templates/checklist (gm-md-slim); truncation disclosure (advisory-fences);
skill files (skill-guidance-pass).

## Verification

Lane: agent

## Blocked by

None (see collision warning).

---

## QA Reports

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
