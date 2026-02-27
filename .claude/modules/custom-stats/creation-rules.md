# Custom Stats — Creation Rules

> Instructions for DM (Claude) when building a new campaign with this module active.
> Run AFTER the user defines tone/setting, BEFORE generating world details.

---

## Step 1: Suggest Stats Based on Genre

Based on the campaign's tone and setting, propose a stat set. Show examples, let the user pick.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CUSTOM STATS SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on your [GENRE] campaign, here are stat suggestions:

  SURVIVAL (Hunger/Thirst/Radiation)
  Tracks resource depletion in a harsh world.
  Drain per hour, consequences at zero.

  MENTAL (Sanity/Stress/Morale)
  Psychological pressure builds over time.
  Events trigger spikes, rest partially restores.

  MAGICAL (Mana/Corruption/Attunement)
  Mana regenerates during rest, corruption grows with dark magic.

  CUSTOM — define your own stats

  → Type numbers to enable (e.g. "1 3") or describe custom stats.
  → Type SKIP to use no custom stats.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Genre presets:**
- Survival (STALKER/Fallout/Metro): Hunger, Thirst, Radiation
- Horror (CoC/Delta Green): Sanity, Stress
- Fantasy: Mana, Fatigue
- Sci-fi: Oxygen, Power, Hull
- Strategy/Civilization: Population, Food, Materials, Knowledge, Faith, Culture
- Custom: ask user what stats matter in their world

> **ВАЖНО**: Любые статы — персонажные, цивилизационные, фракционные — все пишутся в `character.json` в поле `custom_stats`.
> Не создавай отдельных полей типа `civilization_stats` в campaign-overview. Единый источник правды — `custom_stats`.

---

## Step 2: For Each Stat, Ask How It Behaves

For each selected stat, clarify:

1. **Scale**: 0–100 (default) or something else?
2. **Starting value**: Full (100)? Partial? Zero?
3. **Drain rate**: How fast does it drop per hour?
4. **Recovery**: Restored by sleep/rest? By items? Automatically?
5. **Consequences**: What happens at 0 (or max, for accumulation stats)?

Show a summary before writing:

```
  hunger:    0–100, starts 80, -5/hr, items restore, starvation at 0 → -2 HP/hr
  thirst:    0–100, starts 85, -8/hr, items restore, dehydration at 0 → -3 HP/hr
  radiation: 0–∞,  starts 0,  +2/hr in hot zones, anti-rad restores, poisoning at 80

  Confirm? [Y / edit]
```

---

## Step 3: Write Config to Campaign

### 3a. Write `time_effects` to campaign-overview.json

```bash
CAMPAIGN_DIR=$(bash tools/dm-campaign.sh path)
```

For simple stats (no conditions):
```json
{
  "campaign_rules": {
    "time_effects": {
      "enabled": true,
      "effects_per_hour": {
        "hunger": -5,
        "thirst": -8
      },
      "stat_consequences": {
        "starvation": {
          "condition": {"stat": "hunger", "operator": "<=", "value": 0},
          "effects": [
            {"type": "hp_damage", "amount": -2, "per_hour": true},
            {"type": "message", "text": "Hunger takes its toll."}
          ]
        }
      }
    }
  }
}
```

For stats with sleep recovery (use `rules` array instead):
```json
{
  "rules": [
    {
      "stat": "fatigue",
      "per_hour": 5,
      "sleep_restore_per_hour": -20
    },
    {
      "stat": "mana",
      "per_hour": 8,
      "condition": "stat:mana < max"
    }
  ]
}
```

### 3b. Initialize stats in character.json

```python
uv run python -c "
import json

char_path = '[CAMPAIGN_DIR]/character.json'
with open(char_path) as f:
    char = json.load(f)

char['custom_stats'] = {
    'hunger':    {'current': 80, 'min': 0, 'max': 100},
    'thirst':    {'current': 85, 'min': 0, 'max': 100},
    'radiation': {'current': 0,  'min': 0}
}

with open(char_path, 'w') as f:
    json.dump(char, f, indent=2, ensure_ascii=False)
print('[OK] Custom stats initialized')
"
```

---

## Step 4: Confirm and Show Preview

```
  Custom Stats Configured:
  ├─ hunger:    80/100  (-5/hr)
  ├─ thirst:    85/100  (-8/hr)
  └─ radiation: 0       (+2/hr in hot zones)

  Consequences: starvation at hunger=0, dehydration at thirst=0
  Sleep recovery: thirst+hunger do NOT restore during sleep
                  fatigue DOES restore during sleep (-20/hr)
```

---

## Notes

- If user picks SKIP → do NOT set `time_effects.enabled`, do NOT add `custom_stats` to character
- Accumulation stats (radiation, corruption) have no `max` — they climb indefinitely
- Always confirm the config summary before writing
- Stats interact with world narrative: mention them in scene descriptions

---

## Population-Scaled Food (Civilization campaigns)

For civilization/tribe campaigns where food consumption scales with population automatically.

Use `per_hour_formula` instead of `per_hour` — the engine evaluates it each tick using current `custom_stats` values as variables:

```json
{
  "stat": "food",
  "per_hour_formula": "-(population * 2) / 24",
  "description": "Расход еды: population чел * 2 порции / 24ч"
}
```

- Any custom stat name can be used as a variable in the formula
- Evaluated every hour — always reflects current population
- food stored in **absolute units** (portions), NOT percentages
- `max` = storage capacity (e.g. 12000 = 120 days for 50 people at 2/day)

**When food is added** (hunt/trade/harvest):
```bash
bash .claude/modules/custom-stats/tools/dm-survival.sh custom-stat food +[amount]
```
