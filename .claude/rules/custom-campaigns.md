# Supplementary Rules: Custom Campaign Systems

> **Note:** These rules are opt-in extensions for non-standard campaigns. Standard D&D campaigns work exactly as before without these features.
>
> Activated per-campaign via fields in `campaign-overview.json`.

---

## Overview

This document covers three optional systems designed for campaigns that extend beyond traditional D&D mechanics:

1. **Custom Stats & Time Effects** - For survival mechanics, resource management, and non-standard character attributes
2. **Coordinate Navigation & Maps** - For open-world exploration with spatial positioning
3. **Encounter System v6.0** - For dynamic random encounters during travel

All features are backward-compatible and activate only when their respective fields exist in campaign data.

---

## 1. Custom Stats & Time Effects

**Activation:** Set `campaign_rules.time_effects.enabled = true` in `campaign-overview.json`

### Purpose

Enables non-D&D character statistics that change over time, such as:
- Survival needs (hunger, thirst, sleep)
- Environmental hazards (radiation, temperature)
- Civilization resources (population, food stores, gold reserves)
- Psychological states (sanity, morale)

### Character Schema

Custom stats are defined in `character.json`:

```json
{
  "custom_stats": {
    "hunger": {
      "current": 75,
      "min": 0,
      "max": 100
    },
    "thirst": {
      "current": 60,
      "min": 0,
      "max": 100
    },
    "radiation": {
      "current": 15,
      "min": 0,
      "max": 500
    },
    "gold_reserves": {
      "current": 5000,
      "min": 0,
      "max": null
    }
  }
}
```

**Field Notes:**
- `max: null` means no upper limit (useful for resources)
- Stats can be positive or negative (e.g., debt systems)

### Time Effects Engine

Define how stats change per hour in `campaign-overview.json`:

```json
{
  "campaign_rules": {
    "time_effects": {
      "enabled": true,
      "effects_per_hour": {
        "hunger": -2,
        "thirst": -3,
        "radiation": -0.5
      },
      "stat_consequences": [
        {
          "stat": "hunger",
          "threshold": 0,
          "effect": "damage",
          "value": 1,
          "message": "Starving: you take 1 HP damage per hour"
        },
        {
          "stat": "thirst",
          "threshold": 0,
          "effect": "damage",
          "value": 2,
          "message": "Dehydrated: you take 2 HP damage per hour"
        },
        {
          "stat": "radiation",
          "threshold": 100,
          "effect": "condition",
          "value": "Radiation Sickness",
          "message": "Severe radiation exposure causes illness"
        }
      ]
    }
  }
}
```

**How It Works:**
1. When time advances (via `dm-time.sh` or automatic travel time), elapsed hours are calculated
2. Each stat changes by `effects_per_hour × hours_elapsed`
3. Stats are clamped to `[min, max]` ranges
4. Consequences trigger when thresholds are crossed
5. System outputs before/after values and any triggered effects

### CLI Commands

**View Custom Stat:**
```bash
bash tools/dm-player.sh custom-stat hunger
```

**Modify Custom Stat:**
```bash
bash tools/dm-player.sh custom-stat hunger +15
bash tools/dm-player.sh custom-stat thirst -10
```

**Note:** Character name is optional - system auto-detects active character.

**Advance Time (Manual):**
```bash
bash tools/dm-time.sh "Evening" "3rd day" --elapsed 4
```
Manually specify that 4 hours have passed.

**Advance Time (Automatic):**
```bash
bash tools/dm-time.sh "Noon" "3rd day" --precise-time "12:30"
```
System calculates elapsed time from previous timestamp.

**Example Output:**
```
[SUCCESS] Time updated to: Noon (12:30), 3rd day
Custom Stats:
  hunger: 80 → 72 (-8)
  thirst: 70 → 58 (-12)
⚠️ TRIGGERED: "Merchant arrives with news"
```

### Auto-Time on Movement

When locations have `distance_meters` in their connections, `dm-session.sh move` automatically:
1. Calculates travel time: `hours = distance_meters / 1000 / speed_kmh`
2. Advances time with elapsed hours
3. Updates custom stats via time effects
4. Checks and triggers consequences

**Do NOT call `dm-time.sh` manually after `dm-session.sh move` - it's redundant.**

**Default Movement Speed:** 4 km/h (walking pace)
- Override with `speed_kmh` field in `character.json`

**Examples:**
- 200m at 4 km/h = 0.05h = 3 minutes
- 2000m at 4 km/h = 0.5h = 30 minutes
- 3000m at 4 km/h = 0.75h = 45 minutes

### Timed Consequences

Schedule events to trigger after specific time delays:

```bash
bash tools/dm-consequence.sh add "Merchant arrives" "after delay" --hours 24
```

**Without `--hours`:** Event-based trigger only (manual)
**With `--hours`:** Auto-triggers when game time advances past threshold

**Conversion Reference:**
- 1 hour = 1
- 1 day = 24
- 2 days = 48
- 1 week = 168

### Scene Display Format

When custom stats are active, include them in the status bar:

```
================================================================
  LOCATION: The Wastes              TIME: Afternoon (15:30)
  ────────────────────────────────────────────────────────────
  LVL: 5  │  HP: ████████░░░░ 18/24 ✓  │  XP: 1250  │  GP: 27
  Hunger: 72/100  │  Thirst: 58/100  │  Rad: 15/500
================================================================
```

### Use Cases

| Campaign Type | Custom Stats Example |
|---------------|----------------------|
| **STALKER (Post-Apocalyptic)** | hunger, thirst, radiation, awareness |
| **Civilization Builder** | population, food, gold, happiness, research_points |
| **Survival Horror** | sanity, fatigue, infection_level |
| **Space Exploration** | oxygen, fuel, hull_integrity |
| **Economic Sim** | gold, reputation, debt |

---

## 2. Coordinate Navigation & Maps

**Activation:** Locations have `coordinates` field in `locations.json`

### Purpose

Provides spatial positioning for:
- Open-world exploration with realistic distances
- Tactical movement visualization
- Automatic route finding
- Direction-based navigation

### Coordinate System

**Origin:** `(0, 0)` at campaign starting location
**Axes:**
- X-axis: West (negative) / East (positive)
- Y-axis: South (negative) / North (positive)
- Units: meters

**Bearing System:**
- 0° = North
- 90° = East
- 180° = South
- 270° = West

### Adding Locations

**Basic (Manual Coordinates):**
```bash
bash tools/dm-location.sh add "Forest Clearing" "A quiet glade" \
  --coordinates 1500 -800
```

**Auto-Calculated (Bearing + Distance):**
```bash
bash tools/dm-location.sh add "Abandoned Farm" "Ruined homestead" \
  --from "Starting Village" \
  --bearing 90 \
  --distance 2500 \
  --terrain farmland
```

**What Happens Automatically:**
1. Calculates coordinates using polar math (bearing + distance from origin)
2. Creates bidirectional connection with `distance_meters` field
3. Stores reverse bearing for return path
4. Adds terrain metadata

### Path Decision System

When a player tries to reach a location with no direct connection:

**Step 1: Check Cache**
System automatically looks for previous routing decision in `path_preferences`.

**Step 2: If No Decision Exists**
```bash
# View route options
bash tools/dm-location.sh routes "Current Location" "Destination"

# Make interactive decision (permanently cached)
bash tools/dm-location.sh decide "Current Location" "Destination"
```

**Decision Options:**
1. **DIRECT PATH** - Straight line (may cross impassable terrain)
2. **USE EXISTING ROUTE** - Follow established connections
3. **BLOCK THIS ROUTE** - Permanently mark as inaccessible

**Caching:** Once decided, the system never asks again for that route pair.

### Directional Blocking

Prevent movement in specific angular ranges (e.g., cliffs, radiation zones):

```bash
# Block directions 160° to 200° (south-southeast arc)
bash tools/dm-location.sh block "Cliff Edge" 160 200 "Steep cliff drop"

# Remove block
bash tools/dm-location.sh unblock "Cliff Edge" 160 200
```

**Use Cases:**
- Cliffs (block south if cliff is to the south)
- Radiation zones (block entire arc toward reactor)
- Impassable terrain (mountains, lakes, walls)

### Map Visualization

**Full ASCII Map:**
```bash
bash tools/dm-map.sh
```
Shows entire known world with connections.

**Tactical Minimap:**
```bash
bash tools/dm-map.sh --minimap
```
Shows immediate area (current location + nearby).

**Custom Size:**
```bash
bash tools/dm-map.sh --width 120 --height 50
```

**GUI Map (Experimental):**
```bash
bash tools/dm-map.sh --gui
```
Launches Tkinter window with terrain colors and interactive view.

**Map Symbols:**
```
@  = Current location
•  = Other locations
── = Connections
▓  = Fog of war (undiscovered)
```

### Location Schema Example

```json
{
  "Agroprom": {
    "position": "Industrial complex north of starting point",
    "description": "Decaying Soviet-era agricultural facility",
    "coordinates": {
      "x": -1000,
      "y": 3000
    },
    "terrain": "industrial_ruins",
    "connections": [
      {
        "to": "Junkyard",
        "path_description": "Overgrown road",
        "distance_meters": 2000,
        "bearing": 135
      }
    ],
    "blocked_directions": [
      {
        "from_bearing": 270,
        "to_bearing": 310,
        "reason": "Impassable radiation zone"
      }
    ]
  }
}
```

### When to Use Coordinates

**✅ Recommended For:**
- Open-world exploration (STALKER, Fallout-style)
- Hex-based or grid campaigns
- Tactical positioning matters
- Want visual map representation
- Realistic travel time based on distance

**❌ Not Recommended For:**
- Linear dungeon crawls
- Abstract concept-based locations ("The Dreamrealm")
- Theater-of-the-mind narrative style
- Locations are more thematic than physical

---

## 3. Encounter System v6.0

**Activation:** Set `campaign_rules.encounter_system.enabled = true`

### Purpose

Automatic random encounter checks during overland travel, with:
- Distance-based segmentation
- DC scaling by distance and time of day
- Character stat-based modifiers
- DM-controlled encounter types
- Waypoint creation for stopping events

### How It Works

When a character moves between locations:

**1. Path Segmentation**
Travel distance is divided into check segments:

| Distance | Segments |
|----------|----------|
| < 1 km | 1 segment |
| 1-3 km | 1 segment |
| 3-6 km | 2 segments |
| > 6 km | 3 segments |

**2. Encounter Check (Per Segment)**
```
Roll: d20 + character_modifier
Check: Roll >= DC → Safe passage
       Roll < DC  → Encounter triggered
```

**3. DC Calculation**
```
DC = base_dc + (segment_km × distance_modifier) + time_modifier
```
**Capped at 30 maximum**

**Example (STALKER Campaign):**
- Base DC: 8
- Distance modifier: 4
- Time modifier: 0 (Day), +2 (Evening), +4 (Night)
- For 1.5km segment at Day: `DC = 8 + (1.5 × 4) + 0 = 14`

**4. Character Modifier**
Depends on `stat_to_use` in config:

| Stat Type | Formula |
|-----------|---------|
| Custom stat | `(value - 50) // 10` |
| Skill | Value directly |
| D&D ability | `(value - 10) // 2` |

**Example:** `awareness: 70` → modifier `+2`

### Encounter Nature Roll

When encounter triggers, system rolls d20 for category:

| Roll | Category | Description |
|------|----------|-------------|
| 1-8 | Dangerous | Enemies, traps, hostile creatures |
| 9-13 | Neutral | Travelers, animals, natural events |
| 14-20 | Special | Loot, unique discoveries, helpful events |

### DM Decision Prompt

```
======================================================================
  ENCOUNTER (Segment 1/1)
======================================================================
Progress: 1500m / 1500m
Time: 15:30

🎲 Encounter Nature: 16 → Special

DM: What type of encounter?
  1) Combat (creates waypoint)
  2) Social (creates waypoint)
  3) Hazard (creates waypoint)
  4) Loot (auto-resolve)
  5) Flavor (auto-resolve)

Type [1-5]:
```

**Encounter Types:**

| Type | Creates Waypoint? | Effect |
|------|-------------------|--------|
| **Combat** | Yes | Stops journey, creates temporary location for battle |
| **Social** | Yes | Stops journey, creates temporary location for NPC interaction |
| **Hazard** | Yes | Stops journey, creates temporary location for obstacle/anomaly |
| **Loot** | No | DM describes find, journey continues automatically |
| **Flavor** | No | DM describes atmospheric event, journey continues |

### Waypoint Mechanics

When types 1-3 are chosen, system creates a **temporary location** mid-journey:

**Waypoint Structure:**
```json
{
  "waypoint_agroprom_dump_seg1": {
    "is_waypoint": true,
    "position": "On the road between Agroprom and Dump",
    "description": "A point along the journey where an encounter occurred",
    "coordinates": {
      "x": -1500,
      "y": 2000
    },
    "original_journey": {
      "from": "Agroprom",
      "to": "Dump",
      "segment": 1,
      "progress_meters": 1000,
      "remaining_meters": 1000
    },
    "connections": [
      {"to": "Agroprom", "distance_meters": 1000},
      {"to": "Dump", "distance_meters": 1000}
    ]
  }
}
```

**Player Actions at Waypoint:**
- Resolve encounter (combat, talk to NPC, handle hazard)
- Continue forward: `dm-session.sh move "Dump"`
- Return to origin: `dm-session.sh move "Agroprom"`

**After Leaving:** Waypoint is automatically deleted from `locations.json`

**On Map:** Waypoint appears as `@` (current position) between origin and destination.

### Configuration

```json
{
  "campaign_rules": {
    "encounter_system": {
      "enabled": true,
      "min_distance_meters": 300,
      "base_dc": 8,
      "distance_modifier": 4,
      "stat_to_use": "custom:awareness",
      "use_luck": false,
      "time_dc_modifiers": {
        "Morning": 0,
        "Day": 0,
        "Evening": 2,
        "Night": 4,
        "Late Night": 6
      }
    }
  }
}
```

**Parameter Reference:**

| Field | Purpose |
|-------|---------|
| `enabled` | Master toggle |
| `min_distance_meters` | Minimum distance to trigger checks |
| `base_dc` | Base difficulty (lower = more encounters) |
| `distance_modifier` | DC increase per kilometer |
| `stat_to_use` | Format: `custom:name`, `skill:name`, or `ability:name` |
| `use_luck` | Add luck modifier to nature roll (optional) |
| `time_dc_modifiers` | DC adjustment by time of day |

### Balance Guidelines

Choose parameters based on desired encounter frequency:

| Campaign Style | Base DC | Dist Mod | Expected Rate |
|----------------|---------|----------|---------------|
| **Survival (STALKER)** | 8 | 4 | 30-50% per 1-2km |
| **Fantasy Wilderness** | 15 | 3 | 20-30% per 3-5km |
| **Urban/Safe** | 12 | 2 | 10-20% per 5-10km |

**Tuning Tips:**
- Lower base DC → more encounters
- Higher distance modifier → penalties for long journeys
- Higher time modifiers → dangerous nights

### CLI Commands

**Toggle System:**
```bash
bash tools/dm-encounter.sh toggle
```

**Check Configuration:**
```bash
bash tools/dm-encounter.sh status
```

**Manual Check (Testing):**
```bash
bash tools/dm-encounter.sh check "Origin" "Destination" 2000 forest
```
Simulates encounter check for 2km journey through forest terrain.

### DM Guidance

**When to Use Each Type:**

| Type | Example Scenarios |
|------|-------------------|
| **Combat** | Bandit ambush, hostile mutants, territorial animals |
| **Social** | Traveling merchant, refugees, scouts, hermit |
| **Hazard** | Anomaly field, collapsed bridge, radioactive zone, avalanche |
| **Loot** | Hidden cache, abandoned supply drop, artifact location |
| **Flavor** | Distant gunfire, weather change, ruins visible, animal tracks |

**Balancing Frequency:**
- Too many encounters slow pacing
- Too few make travel feel empty
- Vary types to keep interesting
- Use flavor encounters for atmosphere without game impact

**Narrative Integration:**
- Combat: "Figures emerge from the ruins ahead..."
- Social: "You hear voices around the next bend..."
- Hazard: "The Geiger counter starts clicking rapidly..."
- Loot: "Something metallic glints among the rubble..."
- Flavor: "In the distance, you hear the rumble of thunder..."

---

## Backward Compatibility

All three systems are fully backward-compatible. Standard D&D campaigns continue to work without modification.

**Activation Summary:**

| Feature | Activates When |
|---------|---------------|
| Custom stats | `custom_stats` exists in `character.json` |
| Time effects | `campaign_rules.time_effects.enabled = true` |
| Auto-time on move | Connections have `distance_meters` field |
| Timed consequences | Consequence created with `--hours` parameter |
| Coordinate navigation | Locations have `coordinates` field |
| Path decisions | Coordinate system active + no direct path exists |
| Directional blocking | Location has `blocked_directions` array |
| Encounter system | `campaign_rules.encounter_system.enabled = true` |

If these fields don't exist, the system falls back to standard D&D mechanics.

---

## See Also

- **Full Technical Documentation:** `docs/custom-stats-time-effects-plan.md`
- **Core DM Rules:** `CLAUDE.md`
- **Schema Reference:** `docs/schema-reference.md`

---

**Last Updated:** 2026-02-14
