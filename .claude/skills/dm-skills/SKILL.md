---
name: dm-skills
description: Skill-check resolution — when to roll, the DC ladder, fail-forward philosophy, and margin-based consequences. Load whenever the player attempts something uncertain ("I try to..."). Resolution runs through the generic core (d20 vs DC); this is the judgment framework for when/how.
---

# Skill Checks

## When to roll (dice add fun)
- Uncertain outcome — could go either way
- Stakes matter — success/failure changes the story
- Risk of harm — physical, social, or resource loss
- Contested — someone opposes it
- Time pressure

**Don't roll for:** trivial tasks, impossible tasks, routine professional work, or anything with no meaningful consequence for failure.

## Process
1. Declare the DC BEFORE rolling. 2. Roll `uv run python lib/dice.py "1d20+[mod]"` (or via `game_core.resolve_check`). 3. Narrate by margin.

## DC ladder
Trivial 5 · Easy 10 · Moderate 15 · Hard 20 · Very Hard 25 · Nearly Impossible 30.

## Narrate by margin
Nat 20 = exceptional flourish · beat by 10+ = looks easy, extra benefit · success = clean · fail by 1-4 = close, minor setback · fail by 5+ = clear fail + complication · nat 1 = mishap.

## Fail Forward (CRITICAL)
A failed roll NEVER means "nothing happens" — it means "something DIFFERENT happens."
- Failed lockpick? The pick breaks inside — now you need the key or a louder way.
- Failed persuasion? The NPC shares the info... but tips off your enemies.
- Failed stealth? Not caught yet, but you knocked something over — now you're on a timer.
Framework: (1) what did they try? (2) what was the intent? (3) what goes sideways into a NEW situation? (4) what choice does that create?

## Failure consequences (by margin below DC)
- Physical: 1-2 minor setback · 3-5 resource spent/attention drawn · 6-9 minor harm (1d4) · 10+ real harm (1d6+).
- Social: 1-2 unconvinced · 3-5 attitude shifts negative · 6-9 acts against you · 10+ hostile/spreads word.
- Information: 1-2 partial · 3-5 nothing, try another way · 6-9 wrong conclusion believed true · 10+ triggers a ward/wastes time.

For significant failures: `bash tools/dm-consequence.sh add "[what happens]" "[when]" [--trigger-type ...]`.

## Common skills by ability
STR: Athletics · DEX: Acrobatics/Sleight of Hand/Stealth · INT: Arcana/History/Investigation/Nature/Religion · WIS: Animal Handling/Insight/Medicine/Perception/Survival · CHA: Deception/Intimidation/Performance/Persuasion. (A non-D&D kit defines its own skill list in `ruleset.json`.)
