## Level Up

### Trigger
When `dm-player.sh xp` outputs **"LEVEL_UP"**, immediately perform the ceremony.

### Display
```
================================================================
                    * * * LEVEL UP! * * *
================================================================

  [Character Name] has reached LEVEL [X]!

  --------------------------------------------------------

  Through trials and triumphs, your skills have grown.
  You feel power surge through you...

================================================================
```

### Announce Gains
```
  NEW ABILITIES
  --------------------------------------------------------

  + Hit Points: [Roll or average] + [CON mod] = [total] HP gained
  + Proficiency Bonus: [if increased, now +X]

  CLASS FEATURES (Level [X] [Class]):
  + [Feature Name]: [Brief description]

  [If spellcaster:]
  SPELLCASTING
  + Spell Slots: [new slots gained]
  + Spells Known: [new spells to choose, if applicable]
  + Cantrips: [if new cantrip gained]

  [If ASI level (4, 8, 12, 16, 19):]
  ABILITY SCORE IMPROVEMENT
  Choose one:
  > Increase one ability by +2
  > Increase two abilities by +1 each
  > Take a Feat instead

================================================================
```

### Handle Level-Up Choices

**ASI/Feat (levels 4, 8, 12, 16, 19):** Wait for player choice, then manually edit `abilities` in character.json

**Spellcaster with new spells:** List available spells for their level, use `spell-caster` agent if needed, wait for selection

**Subclass selection (usually level 3):** Present subclass options, get player choice before continuing

### XP Thresholds
| Level | XP Required | Key Milestones |
|-------|-------------|----------------|
| 1→2 | 300 | First level-up! |
| 2→3 | 900 | Often subclass selection |
| 3→4 | 2,700 | First ASI/Feat |
| 4→5 | 6,500 | Extra Attack, 3rd-level spells |
| 5→6 | 14,000 | Subclass feature |
| 6→7 | 23,000 | 4th-level spells |
| 7→8 | 34,000 | Second ASI/Feat |
| 8→9 | 48,000 | 5th-level spells |
| 9→10 | 64,000 | Major class features |

### Hit Dice by Class
| Class | Hit Die |
|-------|---------|
| Barbarian | d12 |
| Fighter, Paladin, Ranger | d10 |
| Bard, Cleric, Druid, Monk, Rogue, Warlock | d8 |
| Sorcerer, Wizard | d6 |

---
