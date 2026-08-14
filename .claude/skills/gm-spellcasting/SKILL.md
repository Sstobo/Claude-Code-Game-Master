---
name: gm-spellcasting
description: D&D-kit spellcasting mechanics — spell slots by level, casting resolution, and concentration. Load when a player casts a spell in a dnd5e-kit campaign. Spawn the spell-caster agent for spell details. Non-D&D kits use their own ruleset magic systems.
---

# Spellcasting Mechanics (D&D kit)

**STEP 0 — KIT GUARD.** If the scene-context KIT block is not `dnd5e`, close this skill and resolve magic through the world's own system.

When a player casts a spell: spawn the `spell-caster` agent for details, check slots, resolve.

- **Attack spells:** d20 + spell attack bonus vs AC.
- **Save spells:** target rolls save vs spell save DC.
- **Utility:** apply effect.

## Spell Slots by Character Level
| Lvl | 1st | 2nd | 3rd | 4th | 5th |
|-----|-----|-----|-----|-----|-----|
| 1 | 2 | - | - | - | - |
| 2 | 3 | - | - | - | - |
| 3 | 4 | 2 | - | - | - |
| 4 | 4 | 3 | - | - | - |
| 5 | 4 | 3 | 2 | - | - |
| 7 | 4 | 3 | 3 | 1 | - |
| 9 | 4 | 3 | 3 | 3 | 1 |

## Concentration
One concentration spell at a time. On damage: Con save DC 10 or half the damage (whichever higher) or lose it. A new concentration spell ends the previous.
