---
type: Flow
title: Authoring an original world
description: /new-game builds one stage — kit, voice, a play pack, one street — then grows the world from the table.
sources:
  - { resource: /.claude/commands/new-game.md }
  - { resource: /lib/world_bible.py }
  - { resource: /lib/play_pack.py }
  - { resource: /tools/gm-playpack.sh }
  - { resource: /tools/gm-extract.sh }
  - { resource: /lib/opening_seed.py }
  - { resource: /lib/player_manager.py }
  - { resource: /lib/identity_onboarding.py }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T12:45:56Z }
---

# Authoring an original world

`/new-game` is `/import` with the book replaced by generation. The door is the
same play pack: kit, voice, a primer, one street. There is no fan-out — you author
tonight's one stage, then the world grows AS YOU PLAY. See
[the dream](../conventions/the-dream.md).

The one problem everything upstream of play is aimed at — **any model asked for "a
fantasy world" produces the same world** — is solved at the seed, not by scale. The
anti-generic levers are the **genre bend**, the **voice exemplar** (narration reads
like a real author), and a **World Kit derived from this world** (never a silent 5e
default). A gazetteer authored before anyone sits down does not make a world
distinct; those three do.

## Phases

| Phase | What happens | Gate |
|---|---|---|
| **A — Seed** | genre-aware questionnaire → `world-seed.json` (premise, tone, genre bend, voice, art style, chronicler) | — |
| **B — Skeleton** | slim bible (voice + signature systems + this street), **shown for approval** | play gates on approval |
| **C — Play pack** | draft the kit, then `gm-playpack.sh set` + `stage` — one room, present NPCs, exits, hook, primer | — |
| **D — Handoff** | lock the chronicler + art style, author appearances for the stage, set `session_count: 0` + location from the pack, then the one identity question → `gm-player.sh onboard` | — |

## The stage, not the planet

Phase C writes only what tonight needs. The play pack (`lib/play_pack.py`,
`tools/gm-playpack.sh`) is one location you can stand in, 2–4 people in the room,
the exits you can see, and the hook that will not wait — never a continent. When
play walks toward a name that isn't in the journal yet, `gm-playpack.sh from-book`
materializes it on demand. Do not census ahead.

## Opening the scene

There is no pre-PC spine to open on. The opening comes from the play pack:
`gm-playpack.sh set` writes the room + hook and marks the opening matched, so
`gm-player.sh onboard` leaves it in place (`opening_seed.reseed_opening` fires
only for the legacy plot-spine path, read by both `player_manager.py` and
`identity_onboarding.py`). `/create-character` remains the opt-in full sheet
builder — never the price of entry.

## Growing the world at the table

The campaign file is a **journal of where the table has been**, and it grows
reactively, from play. When a long-game opportunity appears, seed it with the
living-world tools and let it tick: a **threat clock** (`gm-clock.sh`), an **open
thread** (`gm-session.sh end --open-thread`), a new **plot** beat (`plots.json`), or
a **consequence** (`gm-consequence.sh add`) that fires on the right trigger. That is
the campaign's mid- to long-term planning — authored as you run it, not before.

## Related

- [Import a book](import-a-book.md) — the same shelf, a PDF instead of authored canon
- [Onboarding and death](onboarding-and-death.md) — the three-door identity handoff
- [Play a turn](play-turn.md) — the core loop the stage opens into
