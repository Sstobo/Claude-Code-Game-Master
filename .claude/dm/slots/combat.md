## Combat <!-- slot:combat -->

### Trigger Conditions
- Hostile action declared ("I attack...")
- Initiative required
- Hostile creature appears

### Phase 1: Initialization

#### Step 1: Get Enemy Stats [MANDATORY - NEVER SKIP]
```bash
# Option A: Official D&D monster
uv run python features/dnd-api/monsters/dnd_monster.py "[creature]" --combat

# Option B: Launch monster-manual agent for complex encounters
# Use Task tool with subagent_type=monster-manual

# Option C: Quick NPC stats
echo "Enemy: [Name] | HP: [X] | AC: [Y] | Attack: +[Z] | Damage: [dice]"
```

**Common NPC Stats:**
| Type | HP | AC | Attack | Damage |
|------|----|----|--------|--------|
| Guard | 11 | 16 | +3 | 1d6+1 |
| Bandit | 11 | 12 | +3 | 1d6+1 |
| Priest | 27 | 13 | +2 | 1d6 |
| Veteran | 58 | 17 | +5 | 1d8+3 |
| Mage | 40 | 12 | +5 | 1d4+2 |

#### Step 2: Record Combat Start
```bash
bash tools/dm-note.sh "combat" "Combat: [party] vs [enemies] at [location]"
```

### Phase 2: Initiative
```bash
# Roll for each combatant
uv run python lib/dice.py "1d20+[dex_mod]"
```
Track turn order in memory (highest to lowest).

### Phase 3: Combat Rounds

**Player Turn (Standard D&D):**
1. Ask: "Your turn. What do you do?"
2. Resolve action (Attack, Cast Spell, Dash, Dodge, Help, Hide, Ready)
3. Roll attack: `uv run python lib/dice.py "1d20+[attack_bonus]"` vs stated AC
4. If hit, roll damage: `uv run python lib/dice.py "[damage_dice]"`
5. Update enemy HP and narrate

**Enemy Turn:**
1. Choose target (usually nearest/most damaged)
2. State player AC before rolling
3. Roll attack: `uv run python lib/dice.py "1d20+[enemy_attack_bonus]"`
4. If hit, roll damage and update player HP
5. Narrate dramatically

**Party NPC Combat:**
```bash
bash tools/dm-npc.sh hp "Grimjaw" -4    # Damage
bash tools/dm-npc.sh hp "Silara" +2     # Heal
bash tools/dm-npc.sh party              # Check party status
```

### Phase 4: Resolution

When combat ends, do ALL of these:

#### 1. Award XP [MANDATORY]
```bash
bash tools/dm-player.sh xp "[character]" +[amount]
```

**XP by Challenge Rating:**
| CR | XP | CR | XP | CR | XP | CR | XP |
|----|-----|----|----|----|----|----|----|
| 0 | 10 | 3 | 700 | 7 | 2,900 | 13 | 10,000 |
| 1/8 | 25 | 4 | 1,100 | 8 | 3,900 | 14 | 11,500 |
| 1/4 | 50 | 5 | 1,800 | 9 | 5,000 | 15 | 13,000 |
| 1/2 | 100 | 6 | 2,300 | 10 | 5,900 | 17 | 18,000 |
| 1 | 200 | | | 11 | 7,200 | 20 | 25,000 |
| 2 | 450 | | | 12 | 8,400 | | |

**Bonus XP:** Clever tactics (+25%), Creative environment use (+10-25%), Social victory (+50%)

**Non-Combat XP Awards (DM Discretion):**
| Category | XP Range | Examples |
|----------|----------|----------|
| Minor | 10-25 XP | Good roleplay moment, clever idea, minor puzzle |
| Moderate | 50-100 XP | Overcome non-combat challenge, excellent RP, gather key intel |
| Major | 100-250 XP | Solve complex puzzle, diplomatic victory, avoid deadly combat |
| Epic | 250-500 XP | Story milestone, major character growth, significant discovery |

#### 2. Handle Loot [PERSIST BEFORE NARRATING]

```bash
bash tools/dm-player.sh gold "[character]" +[amount]
bash tools/dm-player.sh inventory "[character]" add "[item_name]"
```

**Inventory System:**
- **Stackable Items**: Consumables with quantities (Medkit x3, Ammo 9mm x60, Vodka x2)
- **Unique Items**: Weapons, armor, quest items (one entry per item, no quantities)
- Auto-migrates from old format on first use (creates `.backup`)
- Transactions are atomic - all changes succeed or all fail

#### 3. Record & Advance
```bash
bash tools/dm-note.sh "combat" "[Character] defeated [X] [enemies] at [location]"
bash tools/dm-time.sh "[new_time]" "[date]"
bash tools/dm-consequence.sh check
```

### Combat Modifiers Quick Reference

| Situation | Effect |
|-----------|--------|
| Advantage | Roll 2d20, use higher |
| Disadvantage | Roll 2d20, use lower |
| Cover (half) | +2 AC and Dex saves |
| Cover (3/4) | +5 AC and Dex saves |
| Flanking | Advantage on melee attacks |
| Prone target | Advantage (melee), Disadvantage (ranged) |
| Critical Hit (nat 20) | Double ALL damage dice, then add modifiers |
| Critical Fail (nat 1) | Auto-miss; consider minor mishap (drop weapon, slip) |

### Death & Dying
- **0 HP** → Unconscious, start death saves
- **Death Save**: DC 10 Con save each turn
  - 3 successes = stabilized
  - 3 failures = death
  - Nat 20 = 1 HP and conscious
  - Nat 1 = 2 failures
- **Massive Damage**: Instant death if damage ≥ max HP

<!-- /slot:combat -->

---
