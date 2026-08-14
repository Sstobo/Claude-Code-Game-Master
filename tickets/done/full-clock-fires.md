---
slug: full-clock-fires
title: A threat clock that fills writes its consequence into the world
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: make-the-world-remember
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: _fire_if_filled writes the clock's consequence as [Clock - name] on the transition into full; stdout redirected so --json stays parseable; gm-clock.sh add gained --consequence/--linked-plot.
reviewRounds: null
implementer: claude-fable-5
createdAt: 2026-08-14T02:25:26Z
updatedAt: 2026-08-14T02:25:26Z
---

## Parent

Make the World Remember (prds/make-the-world-remember.md)

## Category

bug

## What to build

A threat clock carries a `consequence` string — what happens when the countdown runs out
(`lib/threat_clocks.py:31-41`). Import seeds it for real: `lib/clock_seed.py:50-58` pulls
the plot's own stated consequence into every generated clock. At runtime that string is
**only ever echoed in a print** (`lib/threat_clocks.py:150-156`) and rendered as a FULL flag
in the brief (`lib/session_manager.py:565-574`). It is never written into the consequence
engine, so a clock filling is a line the GM might notice rather than a beat that arrives.

Work:

1. When a clock reaches full — both paths, `advance()` (`:43-50`) and `tick_time_clocks()`
   (`:52-72`) — write its `consequence` into `ConsequenceManager` once, the same way
   `record_choice` (`:96-107`) already bridges clocks to consequences (local import of
   `ConsequenceManager`, `self._wsd`). Give the text a recognizable prefix in the same
   spirit as `[Choice — ...]`, e.g. `[Clock — <name>] <consequence>`.
2. Guard it: stamp a flag on the clock (e.g. `consequence_fired: true`) when written, and
   never write again while it stays set. A clock sits at full indefinitely and
   `tick_time_clocks` skips full clocks, but `advance()` on an already-full clock must not
   duplicate either. If a clock is reset or extended below full, clearing the flag is the
   correct behavior.
3. A clock with no `consequence` string fires nothing — no placeholder text.
4. `gm-clock.sh add` / the `add` subparser (`lib/threat_clocks.py:128-129`) accepts
   `--consequence` and `--linked-plot`. `add_clock` already takes both parameters and the
   CLI cannot pass either, so hand-made clocks are structurally incapable of carrying the
   payload this ticket delivers.

## Acceptance criteria

- Advancing a clock with a `consequence` to full creates exactly one matching consequence in
  `consequences.json`.
- Advancing or time-ticking again creates none.
- A clock with no `consequence` creates none.
- `gm-clock.sh add "<name>" <segments> --consequence "..."` round-trips into
  `threat-clocks.json`.
- Existing `tick-time` output and the context clock bar are unchanged.
- `docs/modules/living-world.md` (claims `lib/threat_clocks.py`) updated and restamped in the
  same commit — its table currently says the stored consequence "is never written into the
  consequence engine", which this ticket makes false.

## Notes

This closes the loop the module docstring already claims: "A filled clock is the trigger for
a dramatic beat." Firing writes a *pending* consequence; it does not resolve it or force the
GM's hand, consistent with how consequences work everywhere else
(`docs/modules/living-world.md`, "Firing does not resolve").
