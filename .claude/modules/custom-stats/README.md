# custom-stats

**Any custom numeric stat with automatic time-based drift and threshold consequences.**

Not a survival module. A generic stat engine. Hunger and thirst are just two of a hundred things you can define here — mana regeneration, sanity decay, radiation buildup, faction reputation drift, stress accumulation, oxygen depletion, or anything else your campaign needs.

Zero hardcoded stat names. Everything is defined in `campaign_rules`.

---

## CORE vs custom-stats

| Capability | CORE (vanilla) | + custom-stats |
|---|---|---|
| Numeric stats | HP, gold only | Any stat: hunger, mana, sanity, radiation, stress, fuel... |
| Time passing | Clock advances, nothing else changes | Stats drift automatically per elapsed hour |
| Sleep/rest | No mechanics | `--sleeping` flag reverses drain for recovery stats |
| Thresholds | Death at 0 HP only | Any stat hitting any value triggers damage, conditions, or events |
| Conditional effects | None | Rules fire only when conditions are met (e.g., heal only if HP < max) |
| Player sheet | HP + gold | Stat bars shown in `dm-player.sh show` output |
| Timed consequences | Time-based consequences require manual tracking | `--hours N` adds auto-triggering consequences |

---

## How it works

### Middleware hooks

The module intercepts three CORE tools without modifying them:

**`middleware/dm-player.sh`** — adds `custom-stat` and `custom-stats-list` actions to the player tool. Custom stats appear in the character sheet output.

**`middleware/dm-time.sh`** — detects `--elapsed`, `--precise-time`, or `--sleeping` flags on time advance calls. When present, routes through the survival engine so stats tick automatically as time passes.

**`middleware/dm-consequence.sh`** — adds `--hours N` support to consequence tracking. Consequences with a `trigger_hours` value are auto-resolved during time advance.

### Tick simulation

Each tick iterates hour-by-hour (integer steps). For each hour:
1. Evaluate rule conditions — skip the rule if the condition is not met
2. Apply `per_hour` delta to the stat
3. Clamp to `[min, max]`

After all hours are processed, changed values are written to `character.json`. Consequences are checked against the final values.

### Sleep mode

Pass `--sleeping` to any time advance call. Rules with a `sleep_restore_per_hour` field use that value instead of `per_hour`. Useful for stats that recover during rest (fatigue, HP regen, mana) while others continue draining or simply pause.

---

## Configuration

All configuration lives in `campaign-overview.json` under `campaign_rules.time_effects`.

### Minimal (shorthand)

```json
{
  "campaign_rules": {
    "time_effects": {
      "enabled": true,
      "effects_per_hour": {
        "hunger": -5,
        "thirst": -8,
        "mana": 10
      }
    }
  }
}
```

The `effects_per_hour` shorthand generates a simple rule per stat with no conditions.

### Full schema

```json
{
  "campaign_rules": {
    "time_effects": {
      "enabled": true,

      "effects_per_hour": {
        "<stat_name>": <number>
      },

      "rules": [
        {
          "stat": "<stat_name>",
          "per_hour": <number>,
          "sleep_restore_per_hour": <number>,
          "condition": "<condition_expression>"
        }
      ],

      "stat_consequences": {
        "<consequence_id>": {
          "condition": {
            "stat": "<stat_name>",
            "operator": "<= | >= | ==>",
            "value": <number>
          },
          "effects": [
            {"type": "hp_damage", "amount": <number>, "per_hour": true},
            {"type": "condition", "name": "<condition_name>"},
            {"type": "message", "text": "<narrative text>"}
          ]
        }
      }
    }
  }
}
```

**Field notes:**

- `effects_per_hour` and `rules` are mutually exclusive in practice — if `rules` is present, `effects_per_hour` is ignored. Use `rules` when you need conditions or sleep behavior.
- `condition` is a string expression: `"hp < max"`, `"hp >= 10"`, `"stat:hunger <= 20"`, `"stat:mana < max"`. If the condition is false, the rule is skipped for that tick.
- `sleep_restore_per_hour` only applies when `--sleeping` is passed. If omitted, the `per_hour` value is used even during sleep.
- `stat_consequences` are checked after the tick, against final stat values. All matching consequences fire every tick — design thresholds accordingly.
- `hp_damage` with `per_hour: true` multiplies amount by elapsed hours.

### Character data

Custom stats live in `character.json`:

```json
{
  "custom_stats": {
    "<stat_name>": {
      "current": <number>,
      "min": 0,
      "max": 100
    }
  }
}
```

`min` defaults to `0` if omitted. `max` is optional — omit for unbounded stats (e.g., radiation that can climb indefinitely).

---

## Examples by genre

### Survival (STALKER / Fallout)

```json
{
  "effects_per_hour": {
    "hunger": -5,
    "thirst": -8,
    "radiation": 2
  },
  "stat_consequences": {
    "starvation_damage": {
      "condition": {"stat": "hunger", "operator": "<=", "value": 0},
      "effects": [
        {"type": "hp_damage", "amount": -2, "per_hour": true},
        {"type": "message", "text": "Starvation is taking its toll."}
      ]
    },
    "radiation_poisoning": {
      "condition": {"stat": "radiation", "operator": ">=", "value": 80},
      "effects": [
        {"type": "condition", "name": "radiation_poisoning"},
        {"type": "message", "text": "Geiger counter screams. You feel sick."}
      ]
    }
  }
}
```

```json
{
  "custom_stats": {
    "hunger":    {"current": 70, "min": 0, "max": 100},
    "thirst":    {"current": 85, "min": 0, "max": 100},
    "radiation": {"current": 12, "min": 0}
  }
}
```

### Fantasy (mana regeneration + fatigue)

```json
{
  "rules": [
    {
      "stat": "mana",
      "per_hour": 8,
      "condition": "stat:mana < max"
    },
    {
      "stat": "fatigue",
      "per_hour": 5,
      "sleep_restore_per_hour": -20
    }
  ],
  "stat_consequences": {
    "exhausted": {
      "condition": {"stat": "fatigue", "operator": ">=", "value": 80},
      "effects": [
        {"type": "condition", "name": "exhausted"},
        {"type": "message", "text": "Limbs heavy. Penalty to rolls until you rest."}
      ]
    }
  }
}
```

Note: mana only regenerates when below maximum — the condition prevents wasted ticks.

### Horror (sanity drain)

```json
{
  "effects_per_hour": {
    "sanity": -3
  },
  "stat_consequences": {
    "disturbed": {
      "condition": {"stat": "sanity", "operator": "<=", "value": 50},
      "effects": [
        {"type": "message", "text": "Paranoia sets in. Perception checks at disadvantage."}
      ]
    },
    "breakdown": {
      "condition": {"stat": "sanity", "operator": "<=", "value": 10},
      "effects": [
        {"type": "condition", "name": "psychotic_break"},
        {"type": "message", "text": "Reality fractures. The character acts erratically."}
      ]
    }
  }
}
```

### Sci-fi (oxygen + power)

```json
{
  "effects_per_hour": {
    "oxygen":  -15,
    "power":   -8
  },
  "stat_consequences": {
    "suffocation": {
      "condition": {"stat": "oxygen", "operator": "<=", "value": 0},
      "effects": [
        {"type": "hp_damage", "amount": -5, "per_hour": true},
        {"type": "message", "text": "Suit integrity critical. Suffocating."}
      ]
    },
    "systems_offline": {
      "condition": {"stat": "power", "operator": "<=", "value": 0},
      "effects": [
        {"type": "condition", "name": "suit_offline"},
        {"type": "message", "text": "Suit systems offline. Navigation dark."}
      ]
    }
  }
}
```

---

## CLI Reference

All commands are available via `dm-survival.sh` directly, or via `dm-player.sh` (for stat read/write) and `dm-time.sh` (for time advance with stat ticking).

### Time tick

```bash
# Apply stat drift for N hours
dm-survival.sh tick --elapsed 3

# Apply in sleep mode
dm-survival.sh tick --elapsed 8 --sleeping
```

### Time advance (full)

Routes through `dm-time.sh` middleware. Updates clock + ticks stats in one call.

```bash
# Advance by explicit hours
dm-time.sh "Evening" "3rd day" --elapsed 4

# Auto-calculate elapsed from previous precise time
dm-time.sh "Noon" "April 15th" --precise-time "12:30"

# Overnight sleep
dm-time.sh "Morning" "4th day" --elapsed 8 --sleeping
```

When `--precise-time` is given, the engine reads the previously stored `precise_time` from campaign data and calculates elapsed hours automatically.

### Stat inspection and modification

```bash
# Show all custom stats with progress bars
dm-survival.sh status

# List all stats (name + value, no bars)
dm-survival.sh custom-stats-list
dm-survival.sh custom-stats-list "CharacterName"

# Read a single stat
dm-survival.sh custom-stat hunger
dm-survival.sh custom-stat "CharacterName" hunger

# Modify a stat (clamped to min/max)
dm-survival.sh custom-stat hunger -20
dm-survival.sh custom-stat hunger +15
dm-survival.sh custom-stat "CharacterName" thirst -5
```

Via `dm-player.sh` (same underlying call, routed by middleware):

```bash
dm-player.sh custom-stat hunger -20
dm-player.sh custom-stats-list
```

### Timed consequences

```bash
# Add a consequence that auto-fires after N hours
dm-consequence.sh add "Wound becomes infected" "Festering wound applies -2 to all rolls" --hours 24
```

Timed consequences are checked and resolved automatically on each time advance.

---

## File layout

```
.claude/modules/custom-stats/
  module.json              # Module metadata and feature list
  rules.md                 # Optional campaign-specific stat rules for DM reference
  lib/
    survival_engine.py     # Core engine: tick, status, modify, advance_time
  tools/
    dm-survival.sh         # CLI entry point (thin bash wrapper)
  middleware/
    dm-player.sh           # Intercepts custom-stat, custom-stats-list
    dm-time.sh             # Intercepts --elapsed, --precise-time, --sleeping
    dm-consequence.sh      # Intercepts add ... --hours N
  tests/
    test_survival_engine.py
```

---

## Use cases

- Survival games: hunger, thirst, temperature, radiation
- Fantasy RPG: mana regeneration, fatigue, spell slot recovery, corruption
- Horror: sanity decay, dread accumulation, investigation progress
- Sci-fi: oxygen, fuel cells, power, hull integrity
- Social / political: faction reputation drift, trust, influence
- Any time-sensitive mechanic: poison buildup, disease progression, wanted level decay, morale
