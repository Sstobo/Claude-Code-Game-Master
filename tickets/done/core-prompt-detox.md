---
slug: core-prompt-detox
title: The always-on layer stops bossing — beat mandate, failure doctrine, format mandates
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: []
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T18:54:05Z
changedFiles: [CLAUDE.md, lib/session_manager.py, tests/test_lean_core.py, tests/test_get_full_context.py, .claude/commands/gm.md, docs/flows/play-turn.md, docs/modules/scene-context.md, docs/conventions/lean-core-and-skill-routing.md]
reviewRounds: 2
resolution: always-on layer informs — one failure sentence, no beat arithmetic, a few numbered options; prefs kept
updatedAt: 2026-08-14T19:20:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

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

LIVE TREE (user-confirmed 2026-08-14): keep the preference *keys*
(`player_rolls`, `beat_length`, `rag_inspiration`) and their surfacing
lines. Drop the doctrine those hunks added: the always-injected failure
NEVER-list, the adaptive-branch "at most one development", and the
CLAUDE.md beat-arithmetic / pre-send audit / "Failure must TAKE something"
sermon. The opt-in `tight` branch keeps its prescription. "exactly 3" →
"a few numbered options" on both the committed text and the dirty hunks.

## Acceptance criteria

- [x] CLAUDE.md contains no numeric cap on world developments per beat and no pre-send self-audit instruction; player-agency guidance survives.
- [x] `gm-session.sh context` output contains at most one sentence about failure stakes, and no NEVER-list.
- [x] The adaptive pacing line sets no numeric cap; the "tight" preference branch is unchanged.
- [x] Exactly-3 relaxed everywhere it appears (grep); death hand-off keeps three routes, loses the script; no duplicate menu text between CLAUDE.md and gm.md.
- [x] tests/test_lean_core.py + test_get_full_context updated and passing; full suite passes.
- [x] docs claiming these sources (play-turn.md, scene-context.md) restamped where claims move.
- [x] (review) `.claude/commands/gm.md` CHARACTER DEATH names the three routes in prose only (no "Present exactly" / numbered 1–2–3 script) and defers framing to CLAUDE.md.
- [x] (review) After `set_preference("action_menu", True)`, the `choices` confirmation string contains no digit option-count (no "3 numbered"); it matches the context line's "a few numbered".

## Out of scope

gm.md's templates/checklist (gm-md-slim); truncation disclosure
(fence-disclosures); skill files (skill-guidance-pass).

## Verification

Lane: agent

## Blocked by

None (see collision warning).

---

## QA Reports

### 2026-08-14T19:20:00Z — pass [93c4068d]
reviewed: perfect (followup). Death hand-off is prose-only; choices-on confirmation is "a few numbered".

### 2026-08-14T19:14:00Z — verified [gk-t8n2wp]
followup tests: 21 passed (test_lean_core + test_get_full_context)

### 2026-08-14T19:12:00Z — fail [30b41429]
reviewed: needs-changes
- `.claude/commands/gm.md:340` — Death hand-off still says "Present exactly:" plus the numbered 1/2/3 menu script.
- `lib/session_manager.py:1175` — `choices` confirmation still prints "Beats will end with 3 numbered choices."

### 2026-08-14T19:06:00Z — verified [gk-t8n2wp]
Adaptive pacing has no numeric cap; failure is one sentence; tight keeps AT MOST ONE; exactly-3 gone from CLAUDE.md + context + gm.md. Death Protocol keeps three routes, loses the numbered script. Preference keys kept. `uv run pytest tests/` exit 0.

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T19:20:00Z  done: always-on layer informs — one failure sentence, no beat arithmetic, a few numbered options; prefs kept  [gk-t8n2wp]
- 2026-08-14T19:14:00Z  followup review dispatched — death menu + choices confirmation  [gk-t8n2wp]
- 2026-08-14T19:12:00Z  review needs-changes — death menu + choices confirmation; fix delegated  [gk-t8n2wp]
- 2026-08-14T19:06:00Z  verified → in-review, review dispatched  [gk-t8n2wp]

- 2026-08-14T18:55:00Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:54:05Z  claimed  [gk-t8n2wp]
- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
