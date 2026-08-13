---
type: Convention
title: Persist before narrate
description: The rule the whole harness exists to enforce — and the honest state of its enforcement, which is advisory.
sources:
  - { resource: /.claude/settings.json }
  - { resource: /.claude/hooks/post-tool-state-log.sh }
  - { resource: /.claude/hooks/session-autosave.sh }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# Persist before narrate

**Nothing happened until it is written to disk.** Every state change — HP, XP, gold,
inventory, mood, location, condition, consequence, death — is persisted *before* a word of
narration reaches the player. This is what makes a campaign survive a crash, a context
reset, a week away, or a different machine.

The failure it prevents is specific and expensive: the model narrates a transformative
beat, the context window rolls, and the beat never existed. The player loses something they
watched happen.

## Enforcement is advisory. There is no guard.

This convention is worth recording precisely because **nothing blocks a missed persist.**
Two hooks are configured in `.claude/settings.json`, and neither one gates:

| Hook | Event | What it actually does |
|---|---|---|
| `post-tool-state-log.sh` | `PostToolUse` on Bash | appends matching state-write commands to `.ship-it/state-writes.log`. `set +e`, all errors swallowed, unconditional `exit 0` |
| `session-autosave.sh` | `Stop` | runs `gm-session.sh save autosave` when an active campaign exists. Also unconditionally `exit 0` |

The audit log is retrospective evidence, and the autosave is a safety net that catches
state *already written* to `character.json` and friends — it cannot recover a change that
was narrated but never persisted. The discipline is on the author of the turn.

## The audit matcher is a literal list

`post-tool-state-log.sh:18` matches command substrings: `gm-player.sh`, `gm-npc.sh`,
`gm-session.sh move`, `gm-consequence.sh add`, `gm-condition.sh`. Anything else — including
`gm-note.sh`, `gm-plot.sh`, `gm-combat.sh`, and every future tool — is not logged. A quiet
audit log means "no matching command ran", never "nothing was written".

## Ordering inside a beat

Persist-first also fixes ordering *within* the beat, and two cases are called out
explicitly in the project instructions because they are easy to get backwards:

- **Loot is persisted before the loot box is shown.**
- **A death is persisted before it is narrated, and the hand-off menu comes after the
  narration** — see [onboarding and the death hand-off](../flows/onboarding-and-death.md).

## Related

- [The tool wrapper contract](tool-wrapper-contract.md) — the commands that do the persisting
- [A play turn](../flows/play-turn.md) — where this sits in the loop
