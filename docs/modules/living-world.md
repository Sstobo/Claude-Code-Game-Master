---
type: Module
title: The living world — consequences, clocks, world tick
description: The three systems that make the world move on its own, and which of them are actually wired to fire.
sources:
  - { resource: /lib/consequence_manager.py }
  - { resource: /lib/threat_clocks.py }
  - { resource: /lib/world_tick.py }
  - { resource: /lib/time_manager.py }
  - { resource: /tools/gm-time.sh }
  - { resource: /tools/gm-session.sh }
  - { resource: /tools/gm-clock.sh }
generated: { by: cursor-grok-4.6, at: 2026-08-14T19:00:04Z }
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
| World tick | **No** — GM-invoked by design | the developments are a model call; `gm-session.sh world-tick '<json>'` persists them (capped, logged, rollback-able). Before 2026-08-13 `WorldTick` had no caller at all |

So three weeks and ten minutes are not the same pressure: the GM passes how much time
actually elapsed, a same-day hop still costs one segment, and a full clock announces
itself (`⚠ FULL — a dramatic beat is due`) in the tick output and the session brief.
Clocks that must not move on the calendar are declared `advance_on: "event"` and only
ever move by hand.

## A clock that fills fires (since 2026-08-14)

`_fire_if_filled` writes the clock's stored `consequence` into the consequence engine as
`[Clock — <name>] <text>`, the same bridge `record_choice` uses. Before this the text was
only echoed in a print, so a countdown running out was a line the GM might notice rather
than a beat that arrived — while `clock_seed` had been seeding that field from the plot's
own stated consequence on every import.

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

`tick()` stamps `last_fired_key` = `location|time|date` on the consequence and leaves it
**active** (`lib/consequence_manager.py:202-211`). Consequences:

- The same consequence will not re-fire while the scene key is unchanged, so a beat can't
  stutter — but walking away and coming back **re-arms it**, because the key changed.
- The GM can veto a firing narratively and nothing needs undoing; the consequence is
  still there.
- A consequence only leaves `active` via explicit `resolve <id>` or by expiring. A
  campaign that never resolves accumulates a permanently pending list.

At most `limit=2` consequences fire per tick, highest-confidence first.

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
the consequence IDs it added. Both rollbacks are ordered write-then-verify: if the log
write fails, `WorldTick.apply` deletes the consequences it just created rather than leaving
un-rollbackable state (`lib/world_tick.py:49-56`).

## Presence is computed twice, from one drifting field

`tick_from_session` builds its own "who is present" list (`lib/consequence_manager.py:260-269`):
party members are always present, everyone else must have the current location in
`tags['locations']` — the canonical (and, since 2026-08-13, only) location field. In a
pre-unification campaign an NPC tagged only via the legacy `location_tags` is invisible to
`on_npc` triggers until `gm-npc.sh unify-tags` runs — see
[the tag-split gotcha](../gotchas/npc-location-tag-split.md).

## Choices are consequences

`ThreatClockManager.record_choice` (`gm-clock.sh choose "<prompt>" "<fork>"`) writes a
dramatic fork into the consequence engine as `[Choice — <prompt>] <fork>`. That is the
whole wire between "the player picked something at an inflection point" and "it pays off
later". Nothing else records choices — though a choice filed as a `player_choices` fact
now also reaches KEY FACTS, see [scene context](scene-context.md).

## Related

- [Scene context](scene-context.md) — where clocks and pending consequences surface
- [Importing a book](../flows/import-a-book.md) — where clocks and consequences get seeded
