---
type: Convention
title: Lean core, skills on demand
description: Why CLAUDE.md stays thin, what the router is allowed to keep inline, and the kit-awareness trap in three of the eight skills.
sources:
  - { resource: /tests/test_lean_core.py }
  - { resource: /.claude/skills/gm-combat/SKILL.md }
  - { resource: /.claude/skills/gm-craft/SKILL.md }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
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

## Three of the eight skills are D&D-only

`gm-combat`, `gm-levelup`, and `gm-spellcasting` encode 5e — hit dice, spell slots, an XP
table, death saves. Their own frontmatter says so: *"in a campaign whose World Kit is
dnd5e. For non-D&D kits, use the generic core and the active ruleset instead."*

**Nothing enforces that.** No test, no guard, no check inside the skills. Loading
`gm-combat` in a Dune campaign silently imports 5e rules the world never declared, and the
result reads as "the world isn't distinctive" rather than as an error. Check the active kit
before loading a mechanics skill — [game core and World Kit](../modules/game-core-and-world-kit.md)
covers what the kit declares.

The other five — `gm-skills`, `gm-social`, `gm-conditions`, `gm-dungeon`, `gm-craft` — are
kit-agnostic judgment frameworks and load freely.

## Related

- [A play turn](../flows/play-turn.md) — where routing happens in the loop
