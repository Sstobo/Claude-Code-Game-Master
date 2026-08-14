---
type: Convention
title: Lean core, skills on demand
description: Why CLAUDE.md stays thin, what the router is allowed to keep inline, and the kit-awareness trap in three of the eight skills.
sources:
  - { resource: /tests/test_lean_core.py }
  - { resource: /.claude/skills/gm-combat/SKILL.md }
  - { resource: /.claude/skills/gm-skills/SKILL.md }
  - { resource: /.claude/skills/gm-craft/SKILL.md }
  - { resource: /lib/session_manager.py }
generated: { by: cursor-grok-4.6, at: 2026-08-14T19:24:32Z }
verified: { by: cursor-grok-4.6, at: 2026-08-14T18:59:59Z }
---

# Lean core, skills on demand

`CLAUDE.md` is always in context; the eight `gm-*` Skills are not. The core routes; the
Skills hold the mechanics. The alternative — one large always-on ruleset — spends the
model's attention on rules that have nothing to do with the current beat, and it is what
this repo migrated *away* from (the pre-lean `CLAUDE.md` is 1227 lines, in git history).

## The line between router and skill

**Router keeps:** the core loop, persist-before-narrate, the action router table, movement,
output format, the search guide, the memory policy, the golden rules, and stakes/death.
These are needed *every* turn or needed to decide *which* skill to load.

**Skills hold:** anything you need only in a specific moment — combat resolution, spell
slots, condition tables, XP thresholds, dungeon procedure, narration craft.

The practical test is the one the router itself fails first: **an XP-by-CR table inline in
`CLAUDE.md` is the smell.** `test_lean_core.py:34` asserts `"25,000" not in text` for
exactly that reason.

## Enforcement point

`tests/test_lean_core.py` is a real guard, and unusually specific for a documentation rule:

- `CLAUDE.md` must be **under 320 lines** and contain `LEAN CORE`
- it must still contain the load-bearing sections by name (Core Loop, Action Router,
  Movement, Output Format, Search Guide, Auto Memory Policy, Golden Rules, `uv run python`)
- it must name **all eight** skills, so a skill can't be orphaned by a router edit
- every skill must exist with matching `name:` frontmatter
- `gm-craft` must still contain `"Yes, and"` and `"Persist before narrating"` — the one
  content assertion, guarding what the test calls the soul

Adding a skill without adding it to `ALL_SKILLS` and the router leaves it unroutable and
untested.

## Three of the eight skills are D&D-only; STEP-0 defers to the KIT block

`gm-combat`, `gm-levelup`, and `gm-spellcasting` encode 5e — hit dice, spell slots, an XP
table, death saves. Each opens with a **one-line STEP 0**: read the scene-context KIT
block, and unless it is `dnd5e`, close the skill and use the generic core + the active
ruleset. That is context deference, not a tool call — no skill instructs
`world_kit.py info` for what the brief now carries. Enforcement:
`test_dnd_only_skills_carry_the_kit_guard` asserts KIT-block / `dnd5e` deference and
forbids the old info-call. `WorldKit.kit()` still supplies the identity —
`ruleset.json`'s `kit` field, defaulting to `"custom"` when absent, so a legacy or
bespoke world can never accidentally qualify as D&D. A campaign that *wants* the 5e
machinery declares `"kit": "dnd5e"` in its ruleset.

(Until 2026-08-13 nothing enforced the split, and loading `gm-combat` in a Dune campaign
silently imported 5e rules — the failure read as "the world isn't distinctive", not as an
error. Until the KIT block landed, the guard paid a STEP-0 tool call to re-derive what
context now prints.)

The guard is still an instruction a model follows, not a hard interlock — the honest
enforcement tier is "tested prompt", one step below "lint rule".

`gm-skills`, `gm-social`, and `gm-conditions` load freely as judgment frameworks, but
their DC ladders and 5e condition lists apply only when the KIT block says `dnd5e`.
`gm-dungeon` and `gm-craft` stay kit-agnostic.

## Related

- [A play turn](../flows/play-turn.md) — where routing happens in the loop
