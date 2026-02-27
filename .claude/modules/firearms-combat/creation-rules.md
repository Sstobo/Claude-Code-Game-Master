# Firearms Combat — Creation Rules

> Instructions for DM (Claude) when building a new campaign with this module active.
> Run DURING Phase 2 of /new-game (world/tone setup), before character creation.

---

## Step 1: Pick Weapon Preset or Customize

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FIREARMS SYSTEM SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Select weapon set for your campaign:

  [1] STALKER / POST-SOVIET
      AKM, AK-74, SVD, PM Pistol, SPAS-12
      Armor: leather jacket → military armor → exoskeleton

  [2] MODERN MILITARY
      M4A1, SCAR-H, MP5, Glock 17, M249 SAW
      Armor: plate carrier → full plate → EOD suit

  [3] SCI-FI / CYBERPUNK
      Plasma rifle, railgun, smart pistol, heavy bolter
      Armor: light mesh → combat armor → powered exo

  [4] CUSTOM — define weapons manually

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 2: Customize Weapons (if needed)

For each weapon the user wants to add or modify, gather:

| Field | Question |
|-------|----------|
| `damage` | Dice notation? (e.g. `2d8+2`) |
| `pen` | Armor penetration rating? (1–10 scale) |
| `rpm` | Rounds per minute? (pistol ~30, rifle ~600, SMG ~800) |
| `magazine` | Magazine size? (reference only) |
| `type` | assault_rifle / pistol / sniper_rifle / shotgun / smg |

Show a preview table before writing:

```
  Weapon          Damage    PEN   RPM   Type
  ─────────────────────────────────────────
  AK-74           2d6+2     3     650   assault_rifle
  SVD Dragunov    2d10+4    5     30    sniper_rifle
  PM Pistol       2d4+1     1     30    pistol
```

---

## Step 3: Write Firearms Config to Campaign

```bash
CAMPAIGN_DIR=$(bash tools/dm-campaign.sh path)
```

```python
uv run python -c "
import json

overview_path = '[CAMPAIGN_DIR]/campaign-overview.json'
with open(overview_path) as f:
    data = json.load(f)

if 'campaign_rules' not in data:
    data['campaign_rules'] = {}

data['campaign_rules']['firearms_system'] = {
    'weapons': {
        'AK74': {
            'damage': '2d6+2',
            'pen': 3,
            'rpm': 650,
            'magazine': 30,
            'type': 'assault_rifle'
        },
        'SVD': {
            'damage': '2d10+4',
            'pen': 5,
            'rpm': 30,
            'magazine': 10,
            'type': 'sniper_rifle'
        }
    },
    'fire_modes': {
        'full_auto': {
            'penalty_per_shot': -2,
            'penalty_per_shot_sharpshooter': -1
        }
    }
}

with open(overview_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('[OK] Firearms system configured')
"
```

---

## Step 4: Set Character Subclass

If the character is a combat specialist, ask:

```
Combat subclass?

  [1] Стрелок (Sharpshooter / Fighter)
      +2 attack bonus on ranged
      Full-auto penalty halved (-1 per shot vs -2)

  [2] Sniper (Rogue)
      Crit on 19-20 (roleplay rule)
      Double range without penalty

  [3] None — standard D&D attack

```

Write to character.json if subclass selected:
```python
char['subclass'] = 'Стрелок'  # or 'Sniper'
```

---

## Step 5: Confirm Armor Scale

Show the armor protection table for this campaign:

```
  Armor                  AC    PROT
  ────────────────────────────────
  No armor               10    0
  Light jacket           11    1
  Body armor (soft)      13    3
  Military plate         15    5
  Powered exoskeleton    17    7
```

Ask: "Does this fit your setting, or adjust armor ratings?"

---

## Notes

- If user picks CUSTOM weapons: ask for each weapon one by one, keep the table running
- The template at `templates/modern-firearms-campaign.json` has full STALKER presets — read it if needed
- Firearms system is ONLY active when `campaign_rules.firearms_system` exists in campaign-overview.json
- Ammo for starting loadout is handled by inventory-system creation-rules — coordinate if both modules active
