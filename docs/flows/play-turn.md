---
type: Flow
title: A play turn
description: The play loop, the three things that fire unasked, and the rule that a missing face or place is read from the book and written into the journal — not scraped ahead.
sources:
  - { resource: /CLAUDE.md }
  - { resource: /tools/gm-session.sh }
  - { resource: /tools/gm-context.sh }
  - { resource: /tools/gm-enhance.sh }
  - { resource: /.claude/settings.json }
  - { resource: /lib/play_pack.py }
  - { resource: /tools/gm-playpack.sh }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T12:24:29Z }
verified: { by: cursor-grok-4.6, at: 2026-08-14T18:59:59Z }
---

# A play turn

**CONTEXT → DECIDE → EXECUTE → PERSIST → NARRATE.** The order is the product. Everything
the harness adds over "a model pretending to be a GM" lives in the first and fourth steps.

## The loop, concretely

1. **CONTEXT** — the session brief (`gm-session.sh context`) and, when the beat is about a
   place or a person, the place brief (`gm-context.sh`). These are two different commands
   returning almost disjoint data; see [scene context](../modules/scene-context.md).
2. **DECIDE** — route on what the player said. The table in `CLAUDE.md` maps phrasing to a
   Skill; the Skill is loaded on demand rather than living in the always-on core. See
   [lean core and skill routing](../conventions/lean-core-and-skill-routing.md).
3. **EXECUTE** — resolve through the active World Kit, never a hardcoded rule set.
   Dice only ever come from `lib/dice.py`, one roll per command, never inlined.
4. **PERSIST** — write every state change *before* narrating. See
   [persist before narrate](../conventions/persist-before-narrate.md).
5. **NARRATE** — prose length matched to the beat, and the action menu on or off per the
   player's stored preference.

When the beat needs a face or place that is not in the journal yet,
`bash tools/gm-playpack.sh from-book "<name>"`, then RAG, then narrate. Do not
scrape ahead. The campaign file is a journal; `move` already creates a blank
destination, and first visit already asks the book for a brief. See
[the dream](../conventions/the-dream.md).

## Three things fire without anyone asking

This is the part that is easy to forget when reasoning about a turn, because none of it
appears in the transcript:

| Trigger | What fires | Where |
|---|---|---|
| `gm-session.sh move` | consequence tick, then a lore brief on *first* visit to a place with retained book text | `tools/gm-session.sh` |
| `gm-time.sh` | time-clock advance (`threat_clocks.py tick-time`), then consequence tick | `tools/gm-time.sh` |
| every turn end | `session-autosave.sh` Stop hook → `gm-session.sh save autosave` | `.claude/settings.json` |

So moving the party is never *only* moving the party — it can surface a consequence that
changes the scene you were about to narrate. Check the tick output before writing the beat,
not after. See [the living world](../modules/living-world.md).

## The state-write hook is an auditor, not a guard

The `PostToolUse` hook pattern-matches state-writing commands and appends them to
`.ship-it/state-writes.log`. It **never blocks** — `set +e`, every error swallowed,
`exit 0` unconditionally. Its value is retrospective: after a session that lost something,
the log shows whether the persist call was made at all.

Note the matcher is a literal `case` over command substrings
(`.claude/hooks/post-tool-state-log.sh:18`) covering `gm-player.sh`, `gm-npc.sh`,
`gm-session.sh move`, `gm-consequence.sh add`, and `gm-condition.sh`. A new state-writing
tool is invisible to the audit until it is added there.

## Startup is a decision tree, not a greeting

Before the first word to the player, the harness checks: is the venv built (else `/setup`),
does any campaign exist (else route to `/gm` → New Adventure), do campaigns exist with none
active (else campaign selection — `gm-campaign.sh list`, then `switch <name>`), does the
active campaign have a `character.json` (else identity-first onboarding). Each failure has a
specific destination — see [onboarding and the death hand-off](onboarding-and-death.md) and
[install and setup](../playbooks/install-and-setup.md).

The "exists but none active" state is its own branch because it is not a broken install and
`/setup` does not fix it. `world-state/active-campaign.txt` is what every tool resolves state
through; without it `WORLD_STATE_DIR` is empty. The state-reading wrappers
(`gm-session.sh` and `gm-enhance.sh` when given no campaign name) guard on
that and exit with the two commands that fix it, rather than handing the Python layer an
empty path and surfacing a traceback. Usage/help output still prints without a campaign, and
a verb given an explicit campaign name (e.g. `gm-extract.sh draft-bible <campaign>`) still
runs pre-activation because the name is explicit.

## Related

- [Game core and World Kit](../modules/game-core-and-world-kit.md) — what "resolve through the kit" means
- [Illustrating a scene](scene-illustration.md) — the background branch off a narrated beat
