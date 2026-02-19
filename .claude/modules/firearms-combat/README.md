# firearms-combat

Automated firearms combat resolver for the DM System. Replaces vanilla D&D 5e attack mechanics when your campaign involves guns, armor vests, and people who fire 30 rounds in 6 seconds.

---

## What Is This

A standalone module that handles modern/sci-fi combat resolution: RPM-based shot count, penetration vs protection damage scaling, progressive full-auto penalties, and automatic XP tracking. The DM calls `dm-combat.sh` directly when firearms combat occurs — there is no middleware, the module does not intercept CORE tools.

**Supported genres:** STALKER, Fallout wasteland, modern military, cyberpunk, zombie survival.

---

## CORE D&D 5e vs firearms-combat

| Feature | Vanilla CORE (D&D 5e) | firearms-combat |
|---|---|---|
| Attack roll | 1d20 + bonus | 1d20 + DEX mod + proficiency + subclass |
| Damage per round | One dice roll | One dice roll **per shot** |
| Shots per round | 1 (or Extra Attack) | Derived from weapon RPM over 6 seconds |
| Armor | AC threshold | AC threshold + PROT rating that scales damage |
| Ammunition | Not tracked | Deducted automatically |
| Fire modes | None | `single` / `burst` / `full_auto` |
| Crit mechanics | 2x dice on nat 20 | 2x dice on nat 20, applied per-shot |
| XP tracking | Manual | Auto-written to character file |
| Test mode | None | `--test` flag: show result, write nothing |

---

## How It Works

### RPM -> Shots Per Round

A D&D combat round is 6 seconds. The resolver converts weapon RPM into a realistic shot count:

```
shots_per_round = int((rpm / 60) * 6)
```

Available ammo caps the total. Shots are distributed evenly across targets.

Example: AK-74 at 650 RPM -> 65 shots/round theoretical maximum. With 30 rounds available, you fire 30 shots distributed across your targets.

### Penetration vs Protection

Every weapon has a `pen` value. Every armored target has a `prot` value. The comparison determines damage scaling on each hit:

| Condition | Damage Applied |
|---|---|
| `pen > prot` | 100% (full damage) |
| `prot/2 < pen <= prot` | 50% (half damage) |
| `pen <= prot/2` | 25% (quarter damage) |

Example: AKM (`pen 4`) vs Mercenary (`prot 3`) -> `4 > 3` -> full damage.
Example: PM Pistol (`pen 1`) vs Heavy Armor (`prot 5`) -> `1 <= 5/2` -> quarter damage.

### Fire Modes

**`single`** — One attack roll, one damage roll. No penalty. Consumes 1 round.

**`burst`** — 3 shots, progressive penalty per shot:
- Shot 1: no penalty
- Shot 2: -2 to attack (or -1 for Sharpshooter subclass)
- Shot 3: -4 to attack (or -2 for Sharpshooter)

**`full_auto`** — All available shots fired. Each additional shot beyond the first accumulates a cumulative penalty:

```
attack_modifier = base_attack + (shot_index * penalty_per_shot)
```

Default penalty: -2 per shot. With `Стрелок` (Sharpshooter) subclass: -1 per shot.

A character with +7 to attack firing 5 shots full-auto has modifiers: +7, +5, +3, +1, -1.

### Critical Hits

Natural 20 on any shot: double the number of damage dice. The flat bonus is not doubled.

```
Normal:   2d8+2  ->  roll 2d8, add 2
Crit:     4d8+2  ->  roll 4d8, add 2
```

### Attack Bonus Calculation

```
total_attack = DEX_modifier + proficiency_bonus + subclass_bonus
```

Subclass `Стрелок` adds +2 to attack and reduces full-auto/burst penalty from -2 to -1 per shot.

---

## CLI Usage

All combat is resolved through a single command:

```bash
bash .claude/modules/firearms-combat/tools/dm-combat.sh resolve \
  --attacker "Сталкер" \
  --weapon "AK-74" \
  --fire-mode full_auto \
  --ammo 90 \
  --targets "Бандит:14:25:3" "Бандит2:12:20:2"
```

Add `--test` to simulate without writing any changes:

```bash
bash .claude/modules/firearms-combat/tools/dm-combat.sh resolve \
  --attacker "Сталкер" \
  --weapon "SVD" \
  --fire-mode single \
  --ammo 10 \
  --targets "Mercenary:16:30:3" \
  --test
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--attacker` | yes | Character name (must match active character) |
| `--weapon` | yes | Weapon key from `campaign_rules.firearms_system.weapons` |
| `--fire-mode` | yes | `single`, `burst`, or `full_auto` |
| `--ammo` | yes | Rounds available before this combat action |
| `--targets` | yes | One or more targets in `Name:AC:HP:PROT` format |
| `--test` | no | Dry run: print results, do not update character or inventory |

### Target Format

```
Name:AC:HP:Protection
```

Example: `"Бандит:13:20:2"` — enemy named Бандит, AC 13, 20 HP, protection rating 2.

### Output Example

```
====================================================================
  FIREARMS COMBAT RESOLVER
====================================================================
Weapon: AK-74
Base Attack: +6 (Стрелок subclass)
Shots Fired: 30
Ammo Remaining: 60

--------------------------------------------------------------------
TARGET RESULTS:
--------------------------------------------------------------------

Бандит (AC 14, HP 25, PROT 3)
  Shots: 15 | Hits: 8 (including 1 CRITS!)

  Shot #1:  HIT (18+6=24 vs AC 14)
    Damage: 2d6+2 = 9 raw -> PEN 3 vs PROT 3 = HALF -> 4 HP
  Shot #2:  HIT (15+5=20 vs AC 14)
    Damage: 2d6+2 = 11 raw -> PEN 3 vs PROT 3 = HALF -> 5 HP
  ...
  Shot #7:  CRIT! (20+0=20 vs AC 14)
    Damage: 4d6+2 = 18 raw -> PEN 3 vs PROT 3 = HALF -> 9 HP
  Shot #8:  MISS (3-1=2 vs AC 14)

  Total Damage Dealt: 31 HP
  Status: KILLED (overkill: -6)

--------------------------------------------------------------------
SUMMARY:
--------------------------------------------------------------------
Total Damage: 31 HP
Enemies Killed: 1/1
XP Gained: +25
====================================================================

[AUTO-PERSIST] Updated character XP: +25
[AUTO-PERSIST] Ammo remaining: 60
NOTE: Update ammo manually with: bash tools/dm-player.sh inventory
```

---

## Weapon Configuration

Weapons are defined in `campaign-overview.json` under `campaign_rules.firearms_system.weapons`. The module ships with a ready-to-use template at `templates/modern-firearms-campaign.json`.

### Weapon Fields

| Field | Type | Description |
|---|---|---|
| `damage` | string | Dice notation: `"2d8+3"` |
| `pen` | int | Penetration rating (compared against target `prot`) |
| `rpm` | int | Rounds per minute (determines full-auto shot count) |
| `magazine` | int | Magazine capacity (reference only, not enforced by resolver) |
| `type` | string | `assault_rifle`, `pistol`, `sniper_rifle`, `shotgun` |

### Included Weapon Presets (from template)

| Key | Name | Damage | PEN | RPM | Type |
|---|---|---|---|---|---|
| `AKM` | AKM (7.62x39mm) | 2d8+3 | 4 | 600 | Assault rifle |
| `AK74` | AK-74 (5.45x39mm) | 2d6+2 | 3 | 650 | Assault rifle |
| `M4A1` | M4A1 Carbine (5.56x45mm) | 2d6+2 | 3 | 700 | Assault rifle |
| `SVD` | SVD Dragunov (7.62x54mm) | 2d10+4 | 5 | 30 | Sniper rifle |
| `SPAS12` | SPAS-12 Shotgun (12ga) | 3d8+2 | 2 | 40 | Shotgun |
| `Glock17` | Glock 17 (9x19mm) | 2d4+2 | 2 | 60 | Pistol |
| `PM_Pistol` | PM Pistol (9x18mm) | 2d4+1 | 1 | 30 | Pistol |

### Adding a Custom Weapon

Add a new entry to `campaign-overview.json`:

```json
"campaign_rules": {
  "firearms_system": {
    "weapons": {
      "G36C": {
        "damage": "2d6+2",
        "pen": 3,
        "rpm": 750,
        "magazine": 30,
        "type": "assault_rifle"
      }
    }
  }
}
```

---

## Enemy Types

From the template (`templates/modern-firearms-campaign.json`), enemies for modern/STALKER campaigns:

| Enemy | AC | HP | PROT | XP |
|---|---|---|---|---|
| Snork (Mutant) | 14 | 25 | 1 | 25 |
| Bandit | 13 | 20 | 2 | 100 |
| Mercenary | 16 | 30 | 3 | 450 |
| Controller | 12 | 60 | 0 | 1800 |

Pass any enemy as a CLI target directly:

```bash
--targets "Snork:14:25:1" "Mercenary:16:30:3"
```

---

## Armor Reference

| Armor | AC Bonus | PROT |
|---|---|---|
| Leather Jacket | +1 | 1 |
| Medium Body Armor | +3 | 3 |
| Heavy Armor Plate | +5 | 5 |
| Powered Exoskeleton | +7 | 7 |

---

## Subclasses

Two subclasses are defined in the campaign template and interact with the resolver:

**Sharpshooter (`Стрелок`, Fighter subclass)**
- +2 to attack bonus on all ranged attacks
- Full-auto/burst penalty reduced: -1 per shot instead of -2
- Quick Reload as bonus action (roleplay rule, not enforced by resolver)

**Sniper (Rogue subclass)**
- Critical hits on 19-20 (roleplay/DM-adjudicated, resolver uses nat 20 only by default)
- Long Shot: double range without penalty

---

## Use Cases

- **STALKER campaigns** — Duty vs Freedom firefights in the Zone, bandit ambushes, pseudogiant encounters
- **Fallout wasteland** — raider gangs, Brotherhood patrols, super mutant assaults
- **Modern military** — squad-level CQB, urban warfare, hostage rescue
- **Cyberpunk** — corpo hit teams, gang shootouts, Netrunner-backed ambushes
- **Zombie apocalypse** — horde suppression, ammo conservation decisions under fire mode pressure

---

## Architecture Notes

The module imports CORE's `PlayerManager`, `CampaignManager`, and `JsonOperations` directly. CORE has zero knowledge of this module. No middleware is registered — the module does not intercept `dm-attack.sh` or any other CORE tool. The DM (Claude) decides when to call `dm-combat.sh` based on campaign context.

Post-combat state: XP is written automatically to the character file. Ammo must be updated manually with `dm-player.sh inventory` — the resolver prints the remaining count in the output.
