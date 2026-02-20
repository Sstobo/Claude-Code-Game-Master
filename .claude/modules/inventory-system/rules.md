# Inventory System — DM Rules

---

## When to Use

Use `dm-inventory.sh` for ALL inventory/gold/HP/XP/stat changes — never edit character.json manually.

---

## Core Commands

### After combat / loot found

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh loot "[char]" \
  --gold 250 --xp 150 --items "Medkit:2" "Ammo 5.56mm:60"
```

### Player uses item

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[char]" \
  --remove "Medkit" 1 --hp +20
```

### Player buys / sells

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[char]" \
  --gold -500 --add-unique "Platemail Armor (AC 18)"
```

### Player takes damage / gains XP

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[char]" \
  --hp -10 --xp +200
```

### View inventory

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh show "[char]"
```

---

## Flags Reference

| Flag | Purpose |
|------|---------|
| `--gold N` | Add/subtract gold (fails if insufficient) |
| `--hp N` | Modify HP (clamped to 0–max) |
| `--xp N` | Add XP |
| `--add "Item" N` | Add stackable item (merges with existing) |
| `--remove "Item" N` | Remove stackable item (fails if insufficient) |
| `--add-unique "Item"` | Add unique item (weapon, armor, quest) |
| `--remove-unique "Item"` | Remove unique item (fuzzy match) |
| `--stat name N` | Modify custom stat (hunger, radiation, etc.) |
| `--test` | Preview only — validate without writing |

---

## Validation

All-or-nothing: if any part fails (not enough gold, item missing, stat out of bounds) — **nothing is written**. Use `--test` to check before committing.

---

## Item Types

- **Stackable** — consumables with quantity: Medkit, Ammo, Food, Potions
- **Unique** — named items with full stats in the name: `"AK-74 (5.56mm, 2d6+2, PEN 3)"`, `"Leather Armor (AC 11)"`
