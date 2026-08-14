---
slug: opening-seed-no-fake-session
title: Opening seed places the PC; it does not fabricate a session that never happened
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-14T18:52:00Z
updatedAt: 2026-08-14T18:52:00Z
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

- [ ] After `seed_opening` / `reseed_opening`, `session-log.md` contains no
      opening-seed `### Session Ended` block (and any previously marked block
      is gone).
- [ ] `player_position.current_location` is set to the opening location.
- [ ] No spine plot is stamped `active` with an "Opening beat:" event by the
      seed; the hook is available as overview (or fact) data.
- [ ] `reseed_opening` still picks the PC-matched plot for location + hook
      (existing scoring rules stand).
- [ ] tests/test_opening_seed.py rewritten for the new contract and passing;
      full suite passes.
- [ ] Claiming docs restamped (import / new-game / scene-context if they
      describe PREVIOUSLY ON as the opening).

## Out of scope

Smarter plot scoring (already shipped); `get_full_context` doctrine;
session_manager.py preference keys.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-14T18:52:00Z  created → ready  [gk-t8n2wp]
