---
type: Flow
title: Illustrating a scene
description: Beat to picture — the enablement gate, the background agent, and the two auto-injections that keep a campaign on-model.
sources:
  - { resource: /lib/image_gen.py }
  - { resource: /lib/visual_appearance.py }
  - { resource: /tools/gm-image.sh }
  - { resource: /.claude/agents/scene-illustrator.md }
generated: { by: claude-opus-5, at: 2026-08-14T14:46:17Z }
---

# Illustrating a scene

The image model has no memory between calls. Everything that makes a campaign's gallery
look like one artist drew one cast is state on disk, injected into every prompt.

## The path

1. **Gate.** The session brief reports `Scene images: ENABLED` or `DISABLED` based purely
   on `OPENAI_API_KEY` being set. Disabled means never call the tool and never mention
   images — an unmentioned absence, not an apology.
2. **Spawn `scene-illustrator` in the background** with a one-line beat brief and the
   campaign's locked art style passed verbatim. The slow API call stays off the critical
   path; narration continues.
3. The agent pulls appearances (`gm-image.sh appearance "<name>"`), writes the full prompt,
   and calls `gm-image.sh generate --character "<name>"` per character in frame.
4. **Deliver diegetically** — the picture is an artifact made by the in-world chronicler,
   not "here's an image".

## Two injections happen inside `build_prompt`, not in the prompt you write

`build_prompt` (`lib/image_gen.py`) assembles what actually goes to the model, and
`generate_image` calls it. It appends to the caller's prompt:

- **each named character's canonical appearance**, from the 11-field `visual_appearance`
  block, as `Character (render exactly): …`
- **the campaign's locked art style**, from `chronicler.json`, as
  `Consistent art style (campaign signature): …`

Both are belt-and-braces: they fire even on a direct fallback call where the caller forgot.
The art style injection is guarded on the style string not already appearing in the prompt,
which is the right check.

**Both stay on by default, and the default is the right one** — the drift they prevent is
silent and cumulative, so the cost of a redundant injection is nothing and the cost of a
missing one is a gallery that stops looking like one artbook. Two flags open the door for
the beat where the lock is *wrong*, not merely redundant:

- `--no-style-lock` (`gm-image.sh generate`, `image_gen.py`) skips the art-style
  injection — a dream sequence, flashback, or in-world artifact rendered in another
  register.
- `--no-appearance-lock` skips the appearance injection for the **whole frame** — a
  transformation, disguise, or vision where the stored look is deliberately not what's
  in frame.

Use them per-image; neither changes anything on disk, so the next call locks again.

**A flag only governs the auto-append — the prompt author has to cooperate.**
`scene-illustrator` is instructed to open every prompt with the locked style verbatim and
to restate each character's appearance, precisely because the model has no memory. So
suppressing an injection while still writing the suppressed element into the prompt text
changes nothing. `.claude/agents/scene-illustrator.md` carries the matching rule: on a
deliberate break, pass the flag *and* leave that element out of the prompt.

For the common case — **one** character transformed or disguised while the rest of the
frame is normal — the per-character escape is better than the flag: omit `--character` for
that character only, keep it for everyone else, and describe the altered look in prose. The
frame-wide flag is for single-character frames or a whole scene that has left the world's
visual reality.

## The appearance injection fires whenever a character is passed and the lock is on (since 2026-08-13)

`inject_appearances` appends the stored block for every `--character` name, skipping only
an appearance line already present **verbatim** (idempotency). Until 2026-08-13 the guard
tested whether the character's *name* appeared in the prompt — and since beat prompts
naturally name their characters ("Carl swings the club..."), injection was silently
suppressed in the common case and recurring characters drifted off-model. Regression test:
`tests/test_image_prompt_injection.py`.

Practical rule for prompt authors now: just name people and pass `--character` — the
canonical look rides along regardless of how the prompt is worded. The only two ways it
does not ride along are deliberate: not passing `--character` for that person, or
`--no-appearance-lock`.

## The appearance block is a fixed, ordered field list

`VISUAL_FIELDS` is 11 keys: sex, age, race, species, hair, face, eyes, clothing, gear,
demeanor, size. It is fixed so the PC and NPC paths cannot drift apart — one module
(`lib/visual_appearance.py`) normalizes, merges, and formats for both, and the extraction
schema mirrors it deliberately. `race` and `species` are separate on purpose (cultural vs
biological), and "barefoot" belongs under `gear`.

Author a block at character creation; update it when the look changes
(`gm-player.sh set-appearance` / `gm-npc.sh set-appearance`). A character in frame with no
block gets one authored first, not skipped.

## Cost is estimated locally and can be unknown

`_COST` (`lib/image_gen.py:123`) is a hardcoded table keyed by quality × size, used only
for the spend log — nothing is billed here, and an unrecognized combination logs `?`
rather than failing. Defaults are `gpt-image-2`, `medium`, `1536x1024`, each overridable
by env var. `gm-image.sh log` reads the per-campaign `_gen-log.jsonl`.

Logging is wrapped so it can never break a successful generation
(`lib/image_gen.py:194`) — so a missing log line does not mean a missing image.

## Related

- [Authoring a world](author-a-world.md) — where the chronicler and art style are locked
- [Scene context](../modules/scene-context.md) — where the ENABLED/DISABLED line comes from
