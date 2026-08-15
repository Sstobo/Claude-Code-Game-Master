---
type: Convention
title: The dream — holodeck, not gazetteer
description: The campaign file is a journal of where the table has been. The book is the world. Play writes the next page.
sources:
  - { resource: /.claude/commands/import.md }
  - { resource: /.claude/commands/gm.md }
  - { resource: /.claude/skills/gm-craft/SKILL.md }
  - { resource: /lib/opening_seed.py }
  - { resource: /lib/identity_onboarding.py }
  - { resource: /lib/session_manager.py }
  - { resource: /lib/play_pack.py }
  - { resource: /tools/gm-playpack.sh }
generated: { by: cursor-grok-4.6, at: 2026-08-15T11:52:48Z }
---

# The dream

Star Trek holodeck. A fresh D&D table in 1983. Those are the same feeling.

You do not load a wiki. You step through a door. Someone you came to meet is already
in the room, and they talk like themselves. The rest of the kingdom is a name on the
horizon until you walk toward it.

## The invariant

**The book is the adventure.** Index it once (`prepare`). That is the binder on the
GM's chair.

**The campaign JSON is a journal**, not an encyclopedia. It holds who you are, the
room you are in, the people who have walked on, the debts you made. It does not hold
every city the book named.

**Front-loading is the opposite of the fantasy.** A census of locations and items is a
loading screen. Talking to Bêlit on the *Tigress* is the game.

## What session 0 actually is

1. Put the book on the shelf.
2. Ask who they are — or who they came to stand next to.
3. Open *that* page. One stage: this room, the exits you can see, the people in it,
   one hook that will not wait.
4. Play. When a new face or place is needed, `gm-playpack.sh from-book "<name>"`,
   then RAG, then narrate.

The pack lives on `campaign-overview.json.play_pack`. Context renders it as
`--- PRIMER ---`. `gm-playpack.sh stage` writes the room into the journal.

Identity first. Extract last. Extract only the stage.

## What this forbids

Do not scrape the book into NPCs / locations / items / plots "so they're ready."
Do not stub names so a graph looks complete. An unresolved name means *not on stage
yet*. `move` already creates a blank place when you walk; first visit already asks
the book for a brief. That is the loop. Fill the journal from play.

## Related

- [Importing a book](../flows/import-a-book.md) — index, identity, stage
- [A play turn](../flows/play-turn.md) — materialize on need
- [Onboarding](../flows/onboarding-and-death.md) — the holodeck door
