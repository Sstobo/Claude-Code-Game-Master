## id
space-travel

## name
Space Travel

## description
FTL/Mass Effect/The Expanse: the ship is a living organism with resources, the crew is a valuable asset, and the galaxy awaits those who survive the jump.

## genres
sci-fi, space-opera, hard-sci-fi, exploration, military-sci-fi

## recommended_for
Campaigns featuring a ship as a base, interstellar travel, alien races, space combat, and resource management.

## rules

### Ship resources
Four critical ship metrics:
- **Fuel**: consumed by maneuvers and jumps. Refuel at stations/stars/gas giants.
- **Hull**: ship HP, 0-100%. At 50% — leaks, systematic failures. At 25% — critical damage, DC 16 Pilot each turn or lose another 1d6 Hull. At 0% — catastrophic destruction.
- **Oxygen**: -5%/day under normal conditions. Leaks: -10-30%/hour. At 20% — crew panic (-2 to rolls). At 10% — non-suited crew loses consciousness. At 0% — death in 3 rounds.
- **Power**: powers all systems. If Power < 30% — choose what to shut down: weapons/shields/life support/engines.

**Resource consumption during travel:**
```
Fuel_per_jump = base_cost × distance_LY × (1 + damage_modifier)
Oxygen_drain = crew_count × 0.5% per hour
Power_drain = active_systems × power_rating / reactor_output
```

### Jumps (FTL)
FTL types (setting-dependent, choose one):
- **Hyperspace**: Fuel -20 per jump, 1d4 hours in transit. DC 13 Navigation or miss by 1d6 light-years.
- **Wormhole**: Fuel -5 per jump, instantaneous, but only to known nodes. Discovering a new one: DC 18 Science.
- **Warp drive**: Fuel -10/h × distance, continuous flight. Speed 1 LY/hour.

**Emergency jump** (no calculation): DC 16 or random exit point (d100 table). Fuel ×2.
**Gravity wells**: jumping inside a planet's gravity — DC 18 or Hull -2d10.

### Crew as a resource
Every crew member is a Named NPC with a role, skill, and Morale (0-100):
- **Pilot**: Maneuvers DC -2, Dodge +3 in combat
- **Engineer**: Hull Repair +1d8/turn, Emergency Fix DC 12
- **Medic**: Crew recovery, illness DC -4
- **Gunner**: Weapon damage +1d6, Range +25%
- **Navigator**: Jump DC -3, Fuel efficiency +15%
- **Science Officer**: Scan range ×2, Anomaly DC -4

**Crew Morale:**
- 80-100: +2 bonus to specialty
- 50-79: Normal
- 25-49: Follow orders slowly, DC 13 Leadership or task takes ×2 time
- 0-24: Mutiny possible (DC 16 Leadership / turn)

Morale decreases: deaths of comrades (-10), starvation rations (-5/day), mission failure (-5), long flight without rest (-3/week).
Morale increases: victory (+5), bonuses/loot (+5-15), shore leave at a station (+10).

### System reputation
Each star system/faction has a Reputation from -100 to +100:
- **Unknown**: starts at 0, neutral
- **Trusted** (+30+): access to restricted stations, 20% discounts, quests
- **Ally** (+60+): military support, exclusive technology
- **Hostile** (-30 below): inspections, fines, patrol attacks
- **Pirate/enemy** (-60 below): kill-on-sight in system

Reputation affects **trade prices**: ×(1 - reputation/200) of base price. Enemies sell only through intermediaries (+40% markup).

### Space combat
Initiative: d20 + Pilot_modifier.
Turn phases:
1. **Maneuver**: Pilot DC 13 → choose position (Flanking +2, Defensive -2 incoming damage)
2. **Weapons**: Gunner d20 + weapon_bonus vs AC (Hull_armor + Pilot_maneuver_bonus)
3. **Shields**: absorb damage first, regenerate 1d6/turn if Power > 50%

System damage (on crit or Hull < 50%): d6 → 1-2 Engines, 3-4 Weapons, 5 Life Support, 6 Reactor.
**Boarding**: DC 14 Pilot to close in, then tactical combat aboard the ship.

### Planetary operations
Landing: DC 12 Pilot, or automatic at a landing pad.
Atmosphere: check before landing (DC 10 Science or suit required).
Gravity: normal (0.5-1.5g) — no penalties. <0.3g: Acrobatics DC 8 per action. >2g: STR DC 13/hour or Exhaustion.

### Anomalies and events (d20 per system)
- 1: Gravity storm — DC 16 Pilot or Hull -2d10, Fuel ×2 to exit
- 2-3: Unknown signal — investigate (DC 14 Science) or ignore
- 4-5: Pirates — negotiate (Deception DC 13) or fight
- 6-8: Asteroid field — DC 12 Pilot each hour or Hull -1d6
- 9-12: Empty sector (safe)
- 13-15: Abandoned ship — loot, but risk
- 16-17: Trade convoy — opportunity to trade or raid
- 18-19: Technology wreckage — DC 15 Science → random upgrade
- 20: Phenomenon — unique discovery, +20 to Reputation in the nearest system
