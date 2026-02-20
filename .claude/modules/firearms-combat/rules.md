# Firearms Combat — DM Rules

---

## When to Use

When player fires a ranged weapon in combat. Call `dm-combat.sh resolve` instead of standard D&D attack rolls.

**Skip when:** melee combat, magic, single thrown weapons, narrative-only outcomes.

---

## Resolving Combat

```bash
bash .claude/modules/firearms-combat/tools/dm-combat.sh resolve \
  --attacker "[char]" \
  --weapon "AK-74" \
  --fire-mode full_auto \
  --ammo 30 \
  --targets "Bandit:13:20:2" "Bandit:13:20:2"
```

**Target format:** `Name:AC:HP:PROT`

Use `--test` to preview without writing changes.

---

## Fire Modes

- `single` — one shot, no penalty
- `burst` — 3 shots, -2/-4 per shot (Стрелок: -1/-2)
- `full_auto` — all available rounds, -2 cumulative per shot (Стрелок: -1)

---

## Penetration vs Protection

| Condition | Damage |
|-----------|--------|
| PEN > PROT | 100% |
| PEN > PROT/2 | 50% |
| PEN ≤ PROT/2 | 25% |

---

## Critical Hits

Natural 20 → double damage dice (modifiers unchanged). Natural 1 → auto-miss.

---

## After Combat

System auto-writes XP to character. Update ammo manually:

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[char]" \
  --remove "Ammo 5.45mm" [rounds_fired]
```
