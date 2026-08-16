---
type: Module
title: The living world — consequences, clocks, world tick
description: The three systems that make the world move on its own, and which of them are actually wired to fire.
sources:
  - { resource: /lib/consequence_manager.py }
  - { resource: /lib/entity_manager.py }
  - { resource: /lib/threat_clocks.py }
  - { resource: /lib/world_tick.py }
  - { resource: /lib/time_manager.py }
  - { resource: /lib/plot_manager.py }
  - { resource: /lib/session_manager.py }
  - { resource: /tools/gm-time.sh }
  - { resource: /tools/gm-session.sh }
  - { resource: /tools/gm-clock.sh }
  - { resource: /tools/gm-plot.sh }
  - { resource: /.claude/agents/plot-weaver.md }
generated: { by: claude-opus-4-8[1m], at: 2026-08-16T00:00:00Z }
verified: { by: cursor-grok-4.6, at: 2026-08-14T19:13:47Z }
---

# The living world

Three systems claim to run without the player: consequences fire on triggers, threat
clocks tick toward a beat, and a between-sessions world tick advances off-screen
developments. **They are wired to very different degrees.** Verified 2026-08-13:

| System | Automatic trigger | How it actually runs |
|---|---|---|
| Consequences | **Yes** | `gm-session.sh move` and `gm-time.sh` both call `gm-consequence.sh tick` after they write |
| Threat clocks | **Time-clocks: yes** (since 2026-08-13) | `gm-time.sh` runs `threat_clocks.py tick-time` — every `advance_on: "time"` clock gains ticks scaled to elapsed magnitude when `--ticks` / `--duration` is passed (default 1, so Dawn→Noon stays +1). Event clocks stay manual: `gm-clock.sh advance "<name>"`. Filling one fires its consequence (below) |
| World tick | **No** — GM-invoked by design | the developments are a model call; `gm-session.sh world-tick '<json>'` persists every proposal, warns (naming the overflow) when the count exceeds the advisory cap of 3, and stays logged / rollback-able. Before 2026-08-13 `WorldTick` had no caller at all |

So three weeks and ten minutes are not the same pressure: the GM passes how much time
actually elapsed, a same-day hop still costs one segment, and a full clock announces
itself (`⚠ FULL — a dramatic beat is due`) in the tick output and the session brief.
Clocks that must not move on the calendar are declared `advance_on: "event"` and only
ever move by hand.

## A clock that fills fires (since 2026-08-14)

`_fire_if_filled` writes the clock's stored `consequence` into the consequence engine as
`[Clock — <name>] <text>`, the same bridge `record_choice` uses. Before this the text was
only echoed in a print, so a countdown running out was a line the GM might notice rather
than a beat that arrived. The clock's `consequence` field is authored when the clock is
created (`gm-clock.sh`), from the pressure the beat is meant to apply.

Firing is the **transition into full**, not a state check: a clock that was already full
fires nothing, and one reset or extended back below full fires again the next time it
fills. That is what keeps it to once per countdown without a flag to keep in sync
(`consequence_fired` is stamped as provenance, never read as a gate). A clock with no
`consequence` fires nothing.

The write is wrapped in `redirect_stdout(sys.stderr)`: `add_consequence` announces itself
on stdout, and this fires from inside `advance` / `tick-time`, whose `--json` output is
parsed. `gm-clock.sh add` also gained `--consequence` / `--linked-plot`, which `add_clock`
had always accepted and the parser could never pass — so hand-made clocks were
structurally incapable of carrying the payload.

## Firing does not resolve

`tick()` stamps `last_fired_key` = `location|time|date` on newly fired consequences and
leaves them **active**. The stamp is an annotation, not a suppressor: a second tick in
the same scene still reports the match as already-fired (no re-stamp, no new provenance).
Walking away and coming back **re-arms it**, because the key changed.

The fire slice is still `limit=2` (highest-confidence first) so a beat does not stutter
with five payoffs at once — remaining matches are disclosed as matched-not-fired rather
than dropped. Fuzzy near-misses (≥ 0.3, below the 0.5 fire threshold) are advisory and
do not fire. `check_pending(..., world_state)` uses the same disclose-not-hide rule.

- The GM can veto a firing narratively and nothing needs undoing; the consequence is
  still there.
- A consequence only leaves `active` via explicit `resolve <id>` or by expiring. A
  campaign that never resolves accumulates a permanently pending list.

## Two ways a trigger matches, and one that misfires

Structured triggers (`--trigger-type on_location|on_npc|on_time|on_event` with `--match`)
score 1.0 on a substring hit against the corresponding world-state field. Legacy free-text
triggers fall back to word-overlap scoring against the whole scene, and need **≥ 50% of
non-stopword trigger words** present to fire at all. Prefer structured triggers; the fuzzy
path is a compatibility fallback, not a feature.

**The expiry check is a whole-word match against the entire scene text** (`_is_expired`) —
location, time, date, present NPC names, and events concatenated. It was a bare substring
test until 2026-08-13, when `--expiry "dawn"` could self-archive at a place named
*Dawnhollow*; word boundaries now prevent that (regression test in
`tests/test_structured_triggers.py`). The scene-wide scope remains, though: an expiry word
that legitimately appears in any field — an NPC named "Dawn" walking in — still ages the
consequence out, so distinctive expiry strings are still the safer choice.

## Provenance and the one-beat undo

Every firing appends to `provenance` in `consequences.json` (`gm-consequence.sh log`), and
`tick()` writes a `_snapshot` of the pre-fire lists. `rollback` restores that snapshot —
but the snapshot is overwritten by the next tick, so **rollback is exactly one beat deep**.

`WorldTick` keeps a separate, deeper log (`world-tick-log.json`) and rolls back by removing
the consequence IDs it added. `apply` writes every proposal; the cap of 3 is a warning
that names what overflowed, not a silent drop. Both rollbacks are ordered write-then-verify:
if the log write fails, `WorldTick.apply` deletes the consequences it just created rather
than leaving un-rollbackable state (`lib/world_tick.py:62-69`).

## Presence is shared; old campaigns still hide untagged NPCs

`tick_from_session` calls `npcs_present` — the same party-or-exact-tag test as the
session brief and the place brief. In a pre-unification campaign an NPC tagged only
via the legacy `location_tags` is invisible to `on_npc` triggers until
`gm-npc.sh unify-tags` runs — see
[the tag-split gotcha](../gotchas/npc-location-tag-split.md).

## Choices are consequences

`ThreatClockManager.record_choice` (`gm-clock.sh choose "<prompt>" "<fork>"`) writes a
dramatic fork into the consequence engine as `[Choice — <prompt>] <fork>`. That is the
whole wire between "the player picked something at an inflection point" and "it pays off
later". Nothing else records choices — though a choice filed as a `player_choices` fact
now also reaches KEY FACTS, see [scene context](scene-context.md).

## Async plot planning — the plot desk (since 2026-08-16)

Mid/long-game planning gained a live plot-creation path and an async worker. Two facts
that span files:

- **`gm-plot.sh add` is the only run-time way to CREATE a plot** (`plot_manager.add_plot`).
  Before it, `plots.json` was populated solely by the `/import` extractor; the GM could
  only `update`/`complete`/`fail` existing rows. A seeded thread defaults to
  `status: dormant`, so it stays OUT of active STORY THREADS. Advancing it wakes it:
  `update_plot` flips `dormant`/`available` -> `active` (a not-yet-active thread that gets
  progress is now in play). `add` refuses to clobber an existing name — extend that one
  instead.
- **Dormant threads resurface on their own via READY THREADS.** `SessionManager._ready_threads`
  surfaces a dormant plot when one of its linked `npcs` is present (same `npcs_present`
  predicate as everything else), its linked `location` is current, or a clock whose
  `linked_plot` names it is at least half full — rendered as `--- READY THREADS ---` in the
  brief. It only *nudges*; the GM wakes the thread with `gm-plot.sh update`. The plot's
  `npcs`/`locations` are therefore load-bearing metadata, not decoration.

The **`plot-weaver`** agent (`.claude/agents/plot-weaver.md`) is the async front door:
spawned in the background from a one-line seed, it grounds the idea in RAG, weaves it onto
existing entities/edges/clocks (via the WORLD INDEX), and persists ONE dormant thread —
`add` + a `--linked-plot` clock + an `on_npc` surfacing consequence — then returns one line.
It is the story analog of the background scene-illustrator, and it fits "plan as you go,
never pre-build": one small dormant thread, not a gazetteer.

## Related

- [Scene context](scene-context.md) — where clocks, pending consequences, and READY THREADS surface
- [Importing a book](../flows/import-a-book.md) — where clocks and consequences get seeded
