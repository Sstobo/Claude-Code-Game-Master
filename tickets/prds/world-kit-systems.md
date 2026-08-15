---
slug: world-kit-systems
title: World-Kit Systems — signature mechanics, not prose
status: active
version: 1
supersedes: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
---

## Problem Statement

A World Kit declares its `signature_systems` as free-text sentences —
`"sorcery is rare, dreadful, and never safe"`, `"reputation and menace matter
as much as steel"`, `"treasure is almost always cursed or guarded by something
inhuman"`. The GM is told to honor them "by vibes." Nothing rolls. The actual
resolution for every imported world collapses to generic `d20-vs-dc` plus a 5e
character sheet (AC, HP, death saves), so a Conan campaign, a Dune campaign, and
a cyberpunk campaign play mechanically identically. The three things that would
make a world feel like *itself* — a dread/menace track, a price for forbidden
power, a curse on the treasure — exist only as strings the engine can't execute.

`executable-world-kit` (done) made the kit run resolution + harm + progression.
This PRD extends that: turn the *signature* systems into executable, world-named
subsystems the GM actually rolls.

## Solution

A small library of **world-agnostic system primitives** — mechanical building
blocks a kit instantiates and *names* for its world. The kit author (the
`/import` and `/new-game` flows) picks 1–3, names them in the world's own terms,
and they ride into scene context and get rolled at the table like dice, not
honored like vibes.

Four primitives cover the round-table's asks and most genre needs:

- **Named Track** — a meter with threshold consequences. Skinned as Menace,
  Dread, Corruption, Heat, Doom, Notoriety. Advances/relieves on triggers; at
  each threshold the GM is handed a consequence to narrate.
- **Price Roll** — taking a marked action (forbidden sorcery, a risky hack)
  forces a roll for what it *costs* the actor, resolved on a cost ladder.
- **Reaction Roll** — an NPC's opening disposition rolled and modified by a
  track or reputation, so what you're known for changes the room before steel
  is drawn.
- **Guarded / Cursed Payoff** — a roll fired *before* the actor's hand closes on
  a marked treasure: a guardian wakes, a curse attaches, or the prize is clean.

The primitives are generic; the *naming and thresholds* are the kit's. This is
the lever for "exciting systems scoped to THIS world," reusable across every book.

## User Stories

1. As a player, I want the sorcerer's power to visibly cost him something when
   he uses it, so magic feels dreadful the way the source promises.
2. As a player, I want my reputation to open and close doors before I speak, so
   "menace matters as much as steel" is a thing I can feel in play.
3. As the GM, I want the kit's signature systems to hand me a concrete roll and
   consequence, so I stop having to invent mechanics mid-scene.
4. As a world author, I want to pick and name a couple of subsystems at creation,
   so each world plays like itself, not like reskinned 5e.

## Implementation Decisions

- **Primitive library in the core.** Add the four primitives to `game_core.py`
  (resolution/harm sibling), each a small, deterministic, dice-backed function
  with typed inputs/outputs. World-agnostic; no book-specific content.
- **Kit instantiation.** `world_kit.py` / `ruleset.json` gains a `systems` block:
  a list of instantiated primitives `{primitive, name, config}` (e.g.
  `{"primitive":"named_track","name":"Menace","config":{"max":6,"thresholds":[...]}}`).
  The legacy free-text `signature_systems` stays as flavor prose; `systems` is
  the executable layer beside it.
- **Design-first.** The exact roll shape, cost ladder, and threshold schema for
  each primitive are specced before the build ticket is worked (a short design
  note or the first ticket's own design section). No improvising the dice.
- **Scene-context surfacing.** The active kit's instantiated `systems` (name +
  current track values + when they fire) ride into `gm-session.sh context`
  alongside YOUR WORLD'S RULES, so the GM sees them every beat.
- **Authoring at creation.** `/import` and `/new-game` pick 1–3 primitives that
  fit the world's tone/themes and name them. Import can infer from the extracted
  themes; new-game authors from the established tone.
- **Lethality dial.** The kit chooses its harm/death model (5e death-saves vs a
  wound-table vs a lower instant-death threshold) so grim worlds play grim.
- **Character fingerprint.** Kit-aware character creation grants every PC at
  least one signature move drawn from the kit's systems, ending `features: []`.

## Testing Decisions

- Each primitive's dice/threshold behavior is pure and unit-assertable → agent.
- The kit `systems` block persisting and round-tripping through
  `world_kit.py` is assertable → agent.
- The `systems` block appearing in `gm-session.sh context` output → agent.
- A created non-5e PC carrying ≥1 feature → agent.
- The lethality model changing 0-HP behavior per kit config → agent.
- Whether a named track *feels* right in play is GM judgment → manual (spot).

## Out of Scope

- A full genre-specific rules compendium — this is the primitive layer, not a
  library of finished skinned systems for every book.
- Changing the base `d20-vs-dc` resolution or the progression models.
- The World Index / entity roster (separate PRD `world-index`).

## Further Notes

- Round-table verdict (Brennan/Gygax/Mercer, even the lazy-prep dissent
  conceded): "systems scoped to this world" is the one gap that is NOT a
  lazy-prep question — it's real, and it's the headline.
- Builds on `executable-world-kit` and `kit-block-in-context` (both done); reuse
  their kit-in-context plumbing rather than rebuilding it.
