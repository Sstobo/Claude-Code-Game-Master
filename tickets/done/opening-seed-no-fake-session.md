---
slug: opening-seed-no-fake-session
title: Opening seed places the PC; it does not fabricate a session that never happened
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: []
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T18:54:05Z
changedFiles: [lib/opening_seed.py, tests/test_opening_seed.py, tests/test_identity_onboarding.py, tests/test_new_game_parity.py, docs/flows/onboarding-and-death.md, docs/flows/import-a-book.md, docs/flows/author-a-world.md]
reviewRounds: 2
resolution: opening seed sets location + KEY FACT hook; no fabricated session
updatedAt: 2026-08-14T19:26:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

## Category

bug

## What to build

`lib/opening_seed.py` `_opening_block` writes a fake `### Session Ended` into
`session-log.md`. `get_full_context` serves it as PREVIOUSLY ON — a cliffhanger
and "session 0" the player never played. It also stamps a spine plot `active`
with an "Opening beat:" event.

Change the seed to:

1. **Provisional location only** — `player_position.current_location` (and
   reseed still rewrites that location when the PC first exists).
2. **No fabricated session-log.** Do not write a `### Session Ended` block.
   Remove a previously seeded opening-seed marked block if one exists (so
   reseed/import repair does not leave the lie).
3. **Spine/plot as options, not an earned active stamp.** Do not mark a plot
   `active` or append an "Opening beat:" event. Surface the chosen hook as
   data the GM can see without pretending play already started — e.g. an
   `overview.opening_hook` (location + plot name + one-or-two-sentence hook)
   that existing context already has a path to, or a KEY FACT. Prefer a field
   `get_full_context` already renders; do **not** add a new always-on sermon.
   If no existing context channel fits, put the hook on `campaign-overview`
   and add one short "Opening (not yet played):" line — not a fake session.

`reseed_opening` still picks the PC-matched plot for *where you stand* and
*which hook is offered*. It does not start that plot.

Do **not** touch `lib/session_manager.py` unless a single existing context
channel must read the new overview field — if so, stop and report; the
orchestrator owns that file until presence lands.

## Acceptance criteria

- [x] After `seed_opening` / `reseed_opening`, `session-log.md` contains no
      opening-seed `### Session Ended` block (and any previously marked block
      is gone).
- [x] `player_position.current_location` is set to the opening location.
- [x] No spine plot is stamped `active` with an "Opening beat:" event by the
      seed; the hook is available as overview (or fact) data.
- [x] `reseed_opening` still picks the PC-matched plot for location + hook
      (existing scoring rules stand).
- [x] tests/test_opening_seed.py rewritten for the new contract and passing;
      full suite passes.
- [x] Claiming docs restamped (import / new-game / scene-context if they
      describe PREVIOUSLY ON as the opening).
- [x] (review) After `seed_opening` / `reseed_opening`, `get_full_context` includes the chosen hook text (KEY FACTS or a single "Opening (not yet played):" line) and still contains no seed-fabricated `### Session Ended` / PREVIOUSLY ON block.

## Out of scope

Smarter plot scoring (already shipped); `get_full_context` doctrine;
session_manager.py preference keys.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T19:26:00Z — pass [11709d26]
reviewed: perfect (followup). Hook is a plot_local KEY FACT; get_full_context already prints it; no fake Session Ended.

### 2026-08-14T19:16:00Z — fail [6378bb63]
reviewed: needs-changes
- lib/opening_seed.py:214 — `opening_hook` is on campaign-overview only; get_full_context never reads it. Write a KEY FACT so an existing context channel surfaces the hook (do not edit session_manager.py).
Notes (style, non-blocking): unused timestamp arg; _commit_opening still rewrites plots.json.

### 2026-08-14T19:06:00Z — verified [gk-t8n2wp]
Seed sets location + overview.opening_hook; strips fake session-log; does not stamp plots active. Leftover identity/new-game tests updated. `uv run pytest tests/` exit 0.

## History

- 2026-08-14T19:26:00Z  done: opening seed sets location + KEY FACT hook; no fabricated session  [gk-t8n2wp]
- 2026-08-14T19:18:00Z  followup review dispatched — KEY FACT surfaces hook  [gk-t8n2wp]
- 2026-08-14T19:16:00Z  review needs-changes — hook must reach KEY FACTS; fix delegated  [gk-t8n2wp]
- 2026-08-14T19:06:00Z  verified → in-review, review dispatched  [gk-t8n2wp]

- 2026-08-14T18:55:00Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:54:05Z  claimed  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  created → ready  [gk-t8n2wp]
