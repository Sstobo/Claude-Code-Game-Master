# inventory-system

Full-featured inventory manager for the DM System. Adds `dm-inventory.sh` to the CORE toolchain (this tool does not exist in vanilla CORE — the module introduces it entirely) and replaces the primitive string-array approach with a typed, transactional inventory engine.

---

## What is this

Vanilla CORE tracks equipment as a plain JSON array of strings with no quantity, no item identity, and no validation. `inventory-system` replaces that with a structured inventory divided into two categories — stackable consumables with quantities and unique named items — plus unified handling of gold, HP, XP, and custom stats, all wrapped in atomic transactions.

Every operation is validated before being applied. If any part of the transaction fails (insufficient gold, missing item, stat out of bounds), the entire operation is rejected and nothing is written.

---

## CORE vs Module

| Capability | Vanilla CORE | inventory-system |
|---|---|---|
| Tool available | No `dm-inventory.sh` | Full `dm-inventory.sh` CLI |
| Item storage | `"equipment": ["Knife", "Rope"]` | `stackable: {}` + `unique: []` |
| Quantities | Not tracked | Per-item quantity with stack merging |
| Unique items | Not supported | Separate list, fuzzy-match removal |
| Gold changes | Not supported | Validated, fails if insufficient |
| HP / XP changes | Not supported | Clamped to 0/max, atomic with items |
| Custom stats | Not supported | Modify via `--stat`, respects min/max |
| Transaction safety | No | Full rollback on any failure |
| Dry run | No | `--test` flag on any write command |
| Loot shorthand | No | `loot` subcommand, one call |
| Old format migration | N/A | Auto-detects and migrates `equipment` array |

---

## Features

### Atomic transactions

All operations in a single `update` call are validated together before any change is written. If gold is insufficient, an item is missing, or a stat would go out of bounds, the entire call fails with an error and nothing is saved.

```bash
# This either applies all three changes or none of them
bash tools/dm-inventory.sh update Стрелок \
  --remove "AK Патрон 5.45" 30 \
  --gold -200 \
  --hp -3
```

Output on failure:

```
[ERROR] Transaction validation failed:
  - Not enough gold: need 200₽, have 150₽

[ROLLBACK] No changes applied
```

### Stackable items with quantity

Items in `inventory.stackable` are keyed by name and tracked by count. Adding an existing item merges into the existing stack. Removing the last unit deletes the key.

```bash
bash tools/dm-inventory.sh update Стрелок --add "AK Патрон 5.45" 60
bash tools/dm-inventory.sh update Стрелок --remove "Медаптечка" 1
bash tools/dm-inventory.sh update Стрелок --set "Медаптечка" 5
```

### Unique items

Named weapons, artifacts, quest objects, and documents go into `inventory.unique`. They are not stacked. Removal uses fuzzy (case-insensitive substring) matching so you do not need to type the full item name exactly.

```bash
bash tools/dm-inventory.sh update Стрелок --add-unique "Детектор артефактов «Медведь»"
bash tools/dm-inventory.sh update Стрелок --remove-unique "Медведь"
# fuzzy match finds "Детектор артефактов «Медведь»" and removes it
```

### --test dry run

Validate any `update` or `loot` call without writing to disk. Shows exactly what would change and confirms whether validation passes.

```bash
bash tools/dm-inventory.sh update Стрелок \
  --remove "AK Патрон 5.45" 200 \
  --gold -500 \
  --test
```

```
====================================================================
  TEST MODE - VALIDATION PASSED
====================================================================

WOULD APPLY:
  Gold: 2500₽ → 2000₽ (-500)
  - AK Патрон 5.45 x200 (total: 120 → -80)

[TEST] No actual changes applied
```

If validation fails in `--test` mode, it shows the errors and exits non-zero — useful for scripted pre-checks.

### loot shorthand

Award gold, multiple items, and XP in a single call. Useful after a combat encounter or dungeon room.

```bash
bash tools/dm-inventory.sh loot Стрелок \
  --gold 500 \
  --items "AK Патрон 5.45:30" "Медаптечка:2" \
  --xp 150
```

Items are specified as `Name:Quantity`. Items without a colon default to quantity 1. The `loot` command also supports `--test`.

### Custom stat integration

Works with the `custom-stats` module. Any stat defined in `character.custom_stats` can be modified through the same `update` call alongside items and gold. The engine respects the stat's `min` and `max` bounds.

```bash
bash tools/dm-inventory.sh update Стрелок \
  --stat hunger +10 \
  --stat thirst +5
```

If a stat would exceed its max or drop below its min, the whole transaction is rejected.

### show command

Prints a formatted snapshot of the character's full inventory, stats, gold, HP, XP, and custom stats.

```bash
bash tools/dm-inventory.sh show Стрелок
```

```
====================================================================
  INVENTORY: Стрелок
====================================================================
  Gold: 2500₽  |  HP: 18/24  |  XP: 1250/2000  |  Level: 3
====================================================================

STACKABLE ITEMS:
  AK Патрон 5.45 ......... 120
  Медаптечка .............. 3

UNIQUE ITEMS:
  • Детектор артефактов «Медведь»
  • Документы Сидоровича

CUSTOM STATS:
  Hunger .................. 40/100
  Thirst .................. 60/100

====================================================================
```

### Old format migration

If a character has an `equipment` array from vanilla CORE, the first inventory operation auto-detects it, creates a `.json.backup` file, and migrates items into the new `stackable`/`unique` structure using keyword and pattern heuristics. No manual conversion needed.

---

## CLI Reference

```
dm-inventory.sh <command> <character> [options]
```

### update

Modify any combination of inventory, gold, HP, XP, and custom stats in one atomic call.

```
dm-inventory.sh update <char> [--add <item> <qty>] [--remove <item> <qty>]
                               [--set <item> <qty>]
                               [--add-unique <item>] [--remove-unique <item>]
                               [--gold <N>] [--hp <N>] [--xp <N>]
                               [--stat <name> <change>]
                               [--test]
```

All flags are optional and composable. `--add`, `--remove`, `--set`, `--add-unique`, `--remove-unique`, and `--stat` can each appear multiple times in one call.

| Flag | Argument | Description |
|---|---|---|
| `--add` | `<item> <qty>` | Add qty to stackable item (merges with existing) |
| `--remove` | `<item> <qty>` | Remove qty from stackable item (fails if insufficient) |
| `--set` | `<item> <qty>` | Set exact quantity of stackable item |
| `--add-unique` | `<item>` | Add item to unique list (no duplicate) |
| `--remove-unique` | `<item>` | Remove unique item (fuzzy match) |
| `--gold` | `<N>` | Add N to gold (negative to subtract) |
| `--hp` | `<N>` | Add N to current HP (clamped to 0 and max) |
| `--xp` | `<N>` | Add N to current XP |
| `--stat` | `<name> <change>` | Modify custom stat by change amount |
| `--test` | — | Validate and preview only, no write |

### show

```
dm-inventory.sh show <char>
```

Displays full inventory, gold, HP, XP, level, and custom stats.

### loot

```
dm-inventory.sh loot <char> [--gold <N>] [--items <Item:qty> ...] [--xp <N>] [--test]
```

Shorthand for post-encounter awards. `--items` takes one or more `Name:Quantity` tokens.

---

## Data Schema

The module writes to `world-state/campaigns/<campaign>/character.json`:

```json
{
  "name": "Стрелок",
  "level": 3,
  "gold": 2500,
  "hp": {
    "current": 18,
    "max": 24
  },
  "xp": {
    "current": 1250,
    "next_level": 2000
  },
  "inventory": {
    "stackable": {
      "AK Патрон 5.45": 120,
      "Медаптечка": 3
    },
    "unique": [
      "Детектор артефактов «Медведь»",
      "Документы Сидоровича"
    ]
  },
  "custom_stats": {
    "hunger": { "current": 40, "min": 0, "max": 100 },
    "thirst": { "current": 60, "min": 0, "max": 100 }
  }
}
```

`inventory.stackable` — dict of `{ "item name": quantity }`. All values are integers.

`inventory.unique` — list of strings. Order is preserved. No duplicates enforced on add (silently skips if already present). Removal uses case-insensitive substring match.

`custom_stats` — dict managed by the `custom-stats` module. `inventory-system` reads and writes `current`, respects `min` and `max`, but does not create stats — they must already exist.

---

## Use Cases

**Loot-heavy dungeon crawl** — award post-room loot in one `loot` call with gold, ammo, and XP. Use `--test` before applying to confirm nothing overflows.

**Survival with resource tracking** — track food, water, fuel, and medicine as stackable items. Combine with `custom-stats` for hunger/thirst decay applied via `--stat`.

**Trading and economy** — validate purchase transactions before committing: `--remove Currency N --add-unique "Item"` fails atomically if the character cannot afford it.

**Named equipment tracking** — weapons, armor, and artifacts in `unique` survive inventory sorts and audits without getting merged into stacks or losing their descriptions.

**Party shared inventory** — run `update` or `loot` against multiple characters sequentially, or point at a dedicated party character file used as a shared stash.

**Pre-session prep** — use `--test` on planned loot distributions to confirm no character overflows a stat or goes broke before committing to anything.
