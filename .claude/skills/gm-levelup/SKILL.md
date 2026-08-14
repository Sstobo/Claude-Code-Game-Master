---
name: gm-levelup
description: D&D-kit leveling — XP thresholds, the level-up ceremony, hit dice by class, and ASI/feat/subclass handling. Load when gm-player.sh xp reports LEVEL_UP in a dnd5e-kit campaign. Non-D&D kits advance via their ruleset progression model (milestone / resource-axis), not this table.
---

# Level Up (D&D kit)

**STEP 0 — KIT GUARD.** If the scene-context KIT block is not `dnd5e`, close this skill and advance through the kit's progression model.

Trigger: when `gm-player.sh xp` outputs **LEVEL_UP**. Note: thresholds are kit-driven (`player_manager._xp_thresholds`); non-D&D kits do not use this 5e table.

## XP Thresholds
| Level | XP | Milestone |
|-------|------|-----------|
| 1→2 | 300 | first level-up |
| 2→3 | 900 | often subclass |
| 3→4 | 2,700 | first ASI/feat |
| 4→5 | 6,500 | extra attack, 3rd-level spells |
| 5→6 | 14,000 | subclass feature |
| 6→7 | 23,000 | 4th-level spells |
| 7→8 | 34,000 | second ASI/feat |
| 8→9 | 48,000 | 5th-level spells |
| 9→10 | 64,000 | major features |

## Hit Dice by Class
Barbarian d12 · Fighter/Paladin/Ranger d10 · Bard/Cleric/Druid/Monk/Rogue/Warlock d8 · Sorcerer/Wizard d6.

## Ceremony
Announce new level → roll/average HP + Con mod → new class features → spellcasting gains → ASI/feat at 4/8/12/16/19 (wait for player choice, then edit `abilities` in character.json) → subclass at level 3.
