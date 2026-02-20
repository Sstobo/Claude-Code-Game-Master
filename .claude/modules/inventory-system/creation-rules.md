# Inventory System — Creation Rules

> Instructions for DM (Claude) when building a new campaign with this module active.
> Run DURING character creation (after character stats are set).

---

## Step 1: Starting Equipment Philosophy

Based on campaign genre, suggest a starting loadout style:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STARTING INVENTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How does your character start?

  [1] POOR — minimal gear, must scavenge
      A knife, ragged clothes, 10 gold

  [2] STANDARD — balanced starting kit
      Basic weapon, light armor, 50 gold + adventuring gear

  [3] EQUIPPED — ready for action
      Quality weapon, medium armor, 150 gold + full kit

  [4] CUSTOM — define starting items manually

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Genre presets:
- STALKER/Fallout: POOR or EQUIPPED (depending on character background)
- Fantasy adventurer: STANDARD
- Military operative: EQUIPPED
- Amnesiac/prisoner: POOR

---

## Step 2: Build Starting Inventory

Based on genre and choice, propose a concrete item list.

**STALKER/Post-Apocalyptic example (EQUIPPED):**
```
Stackable:
  AK-74 Патрон 5.45mm × 90
  Медаптечка × 2
  Бинт × 3
  Хлеб × 2
  Водка × 1

Unique:
  AK-74 (5.45mm, 2d6+2, PEN 3)
  Куртка сталкера (AC 12, PROT 1)

Gold: 500₽
```

**Fantasy STANDARD example:**
```
Stackable:
  Стрела × 20
  Зелье лечения малое × 2
  Факел × 5
  Рацион × 3

Unique:
  Короткий меч (1d6, фехтование)
  Кожаный доспех (AC 11)
  Рюкзак путника

Gold: 50 GP
```

Always show the list and ask: **"Edit anything or looks good?"**

---

## Step 3: Write Inventory to character.json

```bash
CAMPAIGN_DIR=$(bash tools/dm-campaign.sh path)
```

```python
uv run python -c "
import json

char_path = '[CAMPAIGN_DIR]/character.json'
with open(char_path) as f:
    char = json.load(f)

char['gold'] = [STARTING_GOLD]
char['inventory'] = {
    'stackable': {
        '[Item Name]': [quantity],
    },
    'unique': [
        '[Weapon with stats]',
        '[Armor with AC]'
    ]
}

with open(char_path, 'w') as f:
    json.dump(char, f, indent=2, ensure_ascii=False)
print('[OK] Inventory initialized')
"
```

Or use dm-inventory.sh:
```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "[CharName]" \
  --gold [AMOUNT] \
  --add "Медаптечка" 2 "Патрон 5.45" 90 \
  --add-unique "AK-74 (5.45mm, 2d6+2, PEN 3)" \
  --add-unique "Куртка сталкера (AC 12, PROT 1)"
```

---

## Step 4: Confirm with Preview

After writing, show inventory:

```bash
bash .claude/modules/inventory-system/tools/dm-inventory.sh show "[CharName]"
```

---

## Notes

- Always use `dm-inventory.sh update` (not direct JSON) when character file already exists — avoids clobbering other fields
- Unique items: include ALL stats in the name string (weapon damage, armor AC, etc.)
- If custom-stats module is also active, do NOT set custom_stats here — that's handled by custom-stats creation-rules
- Starting gold should feel appropriate to genre: medieval GP, post-apoc rubles/caps, sci-fi credits
