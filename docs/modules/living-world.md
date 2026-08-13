---
type: Module
title: The living world — consequences, clocks, world tick
description: The three systems that make the world move on its own, and which of them are actually wired to fire.
sources:
  - { resource: /lib/consequence_manager.py }
  - { resource: /lib/threat_clocks.py }
  - { resource: /lib/world_tick.py }
  - { resource: /tools/gm-time.sh }
  - { resource: /tools/gm-session.sh }
generated: { by: claude-fable-5, at: 2026-08-13T14:23:00Z }
verified: { by: claude-fable-5, at: 2026-08-13T14:16:30Z }
---

# The living world

Three systems claim to run without the player: consequences fire on triggers, threat
clocks tick toward a beat, and a between-sessions world tick advances off-screen
developments. **They are wired to very different degrees.** Verified 2026-08-13:

| System | Automatic trigger | How it actually runs |
|---|---|---|
| Consequences | **Yes** | `gm-session.sh move` (`tools/gm-session.sh:112`) and `gm-time.sh` both call `gm-consequence.sh tick` after they write |
| Threat clocks | **No** | Seeded at import by `clock_seed.py`, rendered in the session brief — but nothing calls `advance()`. The GM must run it, and there is no bash wrapper: `uv run python lib/threat_clocks.py advance "<name>"` |
| World tick | **No caller at all** | `WorldTick` has no `main()`, no wrapper, and no reference from any command or skill. Tests are its only caller |

The consequence engine is the one that genuinely runs itself. Treat the other two as
machinery the GM drives deliberately, and don't assume a clock has moved because time
passed.

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
`tags['locations']`. That is the same field the context builder reads, and the same field
with two spellings — see [the NPC location tag split](../gotchas/npc-location-tag-split.md).
An NPC tagged only via `location_tags` is invisible to `on_npc` triggers.

## Choices are consequences

`ThreatClockManager.record_choice` writes a dramatic fork into the consequence engine as
`[Choice — <prompt>] <fork>`. That is the whole wire between "the player picked something
at an inflection point" and "it pays off later". Nothing else records choices.

## Related

- [Scene context](scene-context.md) — where clocks and pending consequences surface
- [Importing a book](../flows/import-a-book.md) — where clocks and consequences get seeded
