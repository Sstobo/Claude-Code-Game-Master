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

See [XP & Rewards](#xp--rewards) for XP awards, and [Loot & Rewards](#loot--rewards) for loot handling and post-combat recording.

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
