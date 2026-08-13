---
slug: story-escape-hatches
title: Overrides for the story the code forbids — resurrection, style breaks, appearance breaks
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T21:30:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md) · Trust the Agent review (artifact 1a6acb14)

## Category

enhancement

## What to build

Right defaults, missing escape hatches:

1. **player_manager.py:463-478 corpse guard** — currently an unconditional
   veto on resurrection (revivify, DCC respawns, divine intervention). Add a
   `revive` verb (`gm-player.sh revive <name> [--hp N] --reason "..."`) that
   clears dead status deliberately and logs the reason; the guard's message
   points at it alongside the Death Protocol. Kit-aware flavor optional
   (a kit may declare death irreversible — then revive warns loudly but the
   GM still decides).
2. **image_gen.py:214-224,249-251** — `--no-style-lock` and
   `--no-appearance-lock` flags on gm-image.sh generate, for dream sequences,
   flashbacks by a different in-world hand, mid-transformation characters.
   Defaults unchanged.
3. **import.md:509 + new-game.md:61 art-style formula** — keep the
   once-per-campaign lock and the "In the style of" prefix (parsed); drop the
   mandatory "two unexpected references" mashup shape to one example
   approach among others.

## Acceptance criteria

- [ ] A killed fixture PC can be revived via the new verb with reason logged; modify_hp works again after; kill→revive→kill round-trips.
- [ ] gm-image.sh generate --no-style-lock produces a prompt without the chronicler style line; --no-appearance-lock skips injection (unit-test the prompt builder, no API call).
- [ ] Style-formula wording softened in both commands; "In the style of" prefix requirement intact.
- [ ] Full suite passes; player-character.md + scene-illustration flow restamped where claims move.

## Out of scope

Death Protocol flow itself; chronicler/persona system; image cost gates.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
