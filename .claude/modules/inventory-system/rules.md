# Inventory System Module

## Purpose

Unified inventory manager with atomic transactions for all character inventory and stats operations.

## Features

- **Atomic Transactions**: All changes succeed together or fail together - no partial updates
- **Stackable Items**: Consumables with quantities (Medkit x3, Ammo 9mm x60, Vodka x2)
- **Unique Items**: Weapons, armor, quest items - one entry per item, no quantities
- **Auto-Migration**: Automatically converts old `equipment` array format on first use
- **Test Mode**: Preview changes without applying them

## Usage

### Update Inventory/Stats

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[character_name]" \
  --gold +150 \
  --hp -10 \
  --xp +200 \
  --add "Medkit" 2 "Ammo 9mm" 30 \
  --remove "Bandage" 1 \
  --add-unique "Magic Sword (+1)" \
  --remove-unique "Old Sword" \
  --stat hunger +20 thirst -15
```

### Test Transaction (Validation Only)

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[character_name]" \
  --gold -500 \
  --add-unique "Platemail Armor (AC 18)" \
  --test
```

### View Full Inventory

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh show "[character_name]"
```

### Quick Loot Command

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh loot "[character_name]" \
  --gold 250 \
  --xp 150 \
  --items "Medkit:2" "Ammo 5.56mm:60"
```

## Flags Reference

| Flag | Purpose |
|------|---------|
| `--gold` | Add or subtract gold (validates non-negative) |
| `--hp` | Modify HP (validates within 0 to max_hp) |
| `--xp` | Add XP (awards only, no subtraction) |
| `--add` | Add stackable items (creates if new, increments if exists) |
| `--remove` | Remove stackable items (validates sufficient quantity) |
| `--set` | Set exact quantity for stackable item |
| `--add-unique` | Add unique item to unique array |
| `--remove-unique` | Remove unique item from unique array (fuzzy match) |
| `--stat` | Modify custom stats (hunger, thirst, radiation, etc.) |
| `--test` | Validation mode - shows what would happen but doesn't apply |

## Item Categories

- **Stackable**: Consumables with quantities
  - Examples: Medkit, Ammo, Food, Bandages, Potions
  - Format: Quantity counter
  - Auto-stacks when adding multiples

- **Unique**: One-off items
  - Examples: Weapons with stats, Armor with AC, Quest items, Artifacts
  - Format: Full description with stats
  - No quantity field

## Examples

### Post-Combat Loot

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "Grimjaw" \
  --gold +250 \
  --xp +150 \
  --add "Medkit" 2 "Ammo 5.56mm" 60 \
  --add-unique "M4A1 Carbine (5.56mm, 2d8+2, PEN 3)"
```

### Use Consumables

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "Silara" \
  --remove "Medkit" 1 \
  --hp +20
```

### Validate Before Purchase

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "Conan" \
  --gold -500 \
  --add-unique "Platemail Armor (AC 18)" \
  --test
```

## Validation

The system automatically validates:
- Sufficient gold before spending
- HP stays within [0, max_hp] range
- Sufficient item quantities before removal
- Custom stats stay within [min, max] ranges
- All items exist before removal

If validation fails, **no changes are applied** and detailed error messages are shown.

## Migration

On first use, if a campaign has the old `equipment` array format:
1. Creates `character.json.backup` with timestamp
2. Parses item quantities from names (e.g., "Medkit ×3")
3. Categorizes weapons/armor/quest items as unique
4. Creates new `inventory` structure with `stackable` and `unique` sections
5. Removes old `equipment` field

No manual intervention needed - migration is automatic and creates backups.

## Integration

This module is a **self-contained feature** and does NOT require `campaign_rules` configuration. It works with any campaign that has a `character.json` file.

For campaigns with custom stats (STALKER, Civilization, etc.), the `--stat` flag can modify those stats directly.
