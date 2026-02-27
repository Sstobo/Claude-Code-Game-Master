## Skill Checks

### When to Roll
**Roll when dice add fun:**
- Uncertain outcome - could go either way
- Stakes matter - success/failure changes the story
- Risk of harm - physical danger, social embarrassment, resource loss
- Contested action - someone opposes the attempt
- Time pressure - rushing increases chance of failure

**Don't roll for:**
- Trivial tasks (opening unlocked door)
- Impossible tasks (outrunning a horse on foot)
- Routine professional work
- No meaningful consequence for failure

### The Roll Process
1. **Declare DC BEFORE rolling**
   ```bash
   echo "[Skill] check - DC [X]"
   ```
2. **Roll the check**
   ```bash
   uv run python lib/dice.py "1d20+[modifier]"
   ```
3. **Narrate based on margin**

### Narrate Result by Margin
| Result | Narration Style |
|--------|-----------------|
| Natural 20 | Exceptional success - impressive flourish |
| Success by 10+ | Impressive - looks easy, extra benefit |
| Success | Task accomplished cleanly |
| Failure by 1-4 | Close - almost worked, minor setback |
| Failure by 5+ | Clear failure - complication occurs |
| Natural 1 | Potential mishap - something goes wrong |

### DC Guidelines
| Difficulty | DC |
|------------|-----|
| Trivial | 5 (rarely roll) |
| Easy | 10 |
| Moderate | 15 |
| Hard | 20 |
| Very Hard | 25 |
| Nearly Impossible | 30 |

### Failure Consequences

**Physical Actions:**
| Margin Below DC | Consequence |
|-----------------|-------------|
| 1-2 | Minor setback (takes longer, makes noise) |
| 3-5 | Clear fail - resource spent, attention drawn |
| 6-9 | Rough fail - minor harm (1d4 damage) or complication |
| 10+ | Bad fail - real harm (1d6+ damage) or major complication |

**Social Actions:**
| Margin Below DC | Consequence |
|-----------------|-------------|
| 1-2 | NPC unconvinced but not offended |
| 3-5 | NPC annoyed, attitude shifts negative |
| 6-9 | NPC takes action against party's interests |
| 10+ | NPC becomes hostile or spreads word |

**Information Actions (Arcana, History, Investigation, etc.):**
| Margin Below DC | Consequence |
|-----------------|-------------|
| 1-2 | Partial info, some details missing |
| 3-5 | No info, need different approach |
| 6-9 | Wrong conclusion (believed to be true) |
| 10+ | Triggers ward, alerts guardian, or wastes significant time |

For significant failures, add a consequence:
```bash
bash tools/dm-consequence.sh add "[what happens]" "[when it triggers]"
```

### Fail Forward Philosophy

A failed roll should **NEVER** mean "nothing happens" — it means "something DIFFERENT happens."

- **Failed lockpick?** The pick breaks inside — now you need the key, or a louder method.
- **Failed persuasion?** The NPC shares the info... but also tips off your enemies.
- **Failed stealth?** You're not caught yet, but you knocked something over — now you're on a timer.
- **Failed arcana check?** You misidentify the rune and trigger a minor ward.

Every failure is a new story direction, not a dead end. When a check fails, ask yourself: *"What's the most interesting thing that could go wrong?"*

**Quick framework for unexpected failures:**
1. What did they try? (the skill)
2. What was the intent? (what they hoped to achieve)
3. What goes sideways? (not just "you fail" — what NEW situation are they in?)
4. How does this create a choice? (the player should have a new decision to make)

### Common Skills by Ability
- **STR**: Athletics
- **DEX**: Acrobatics, Sleight of Hand, Stealth
- **INT**: Arcana, History, Investigation, Nature, Religion
- **WIS**: Animal Handling, Insight, Medicine, Perception, Survival
- **CHA**: Deception, Intimidation, Performance, Persuasion

---
