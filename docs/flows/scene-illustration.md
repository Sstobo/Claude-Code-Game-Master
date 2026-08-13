---
type: Flow
title: Illustrating a scene
description: Beat to picture — the enablement gate, the background agent, the two auto-injections that keep a campaign on-model, and the one that quietly doesn't fire.
sources:
  - { resource: /lib/image_gen.py }
  - { resource: /lib/visual_appearance.py }
  - { resource: /tools/gm-image.sh }
  - { resource: /.claude/agents/scene-illustrator.md }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
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

## Two injections happen inside `generate_image`, not in the prompt you write

`lib/image_gen.py:226-240` appends to the caller's prompt:

- **each named character's canonical appearance**, from the 11-field `visual_appearance`
  block, as `Character (render exactly): …`
- **the campaign's locked art style**, from `chronicler.json`, as
  `Consistent art style (campaign signature): …`

Both are belt-and-braces: they fire even on a direct fallback call where the caller forgot.
The art style injection is guarded on the style string not already appearing in the prompt,
which is the right check.

## The appearance injection is guarded on the character's *name*

```python
if line and cname.strip().lower() not in prompt.lower():
```

The guard means: **if the character's name already appears anywhere in the prompt, the
canonical appearance is not injected.** The intent is "the caller already spelled them
out", but the natural way to write a beat prompt is to name people — *"Carl swings the
club at the Terror Clown"* — and that phrasing silently suppresses Carl's stored
appearance for that image. He renders as whatever the model imagines.

Practical rule for prompt authors: either describe the character inline in full, or refer
to them without the stored name and let `--character` do the work. If a recurring
character drifts off-model between images, this guard is the first thing to check.

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
