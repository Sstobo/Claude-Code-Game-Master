# Documentation: Custom Stats, Time Effects, and Automatic Movement

**Status:** IMPLEMENTED
**Date:** 2026-02-12
**Version:** 2.0 (with automatic time calculation during movement)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Schemas](#data-schemas)
4. [Automatic Movement](#automatic-movement)
5. [CLI Commands](#cli-commands)
6. [Usage Examples](#usage-examples)
7. [Backward Compatibility](#backward-compatibility)

---

## Overview

### What's Implemented:

1. **Custom stats** in `character.json` (hunger, thirst, radiation, sleep, and any others)
2. **Time effect rules** in `campaign-overview.json` (automatic stat changes over time)
3. **Automatic effect application** when time changes
4. **Auto-check consequences** with time triggers (`--hours`)
5. **Automatic time calculation** during movement between locations
6. **Auto-detection of active character** (no need to specify name in commands)
7. **Character speed** in `character.json` (for travel time calculation)
8. **Distances between locations** in `locations.json`

### Supported Campaign Types:

- **STALKER** (hunger, thirst, radiation, fatigue)
- **Civilization** (population, resources, culture)
- **Standard D&D** (no custom stats, works as before)

---

## Architecture

### Data Flow During Movement:

```
┌─────────────────────────────────────────────────────┐
│ Claude Code (DM)                                    │
│ bash tools/dm-session.sh move "Junkyard"           │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ lib/session_manager.py::move_party()                │
│                                                     │
│ 1. Read locations.json → find distance_meters      │
│ 2. Read character.json → get speed_kmh             │
│ 3. Calculate: elapsed_hours = distance / speed     │
│ 4. Update player_position                          │
│ 5. Call time_manager.update_time(elapsed_hours)    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ lib/time_manager.py::update_time()                  │
│                                                     │
│ 1. Calculate new precise_time (08:00 → 08:30)      │
│ 2. Update time_of_day based on hour                │
│ 3. Apply time_effects (hunger -2/h, thirst -3/h)   │
│ 4. Check stat_consequences (hunger=0 → HP damage)  │
│ 5. Check time-based consequences (triggers)        │
│ 6. Save campaign-overview.json                     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ OUTPUT:                                             │
│ [SUCCESS] Party moved from Cordon to Junkyard      │
│ [TIME] Travel time: 30 minutes (0.5 hours)         │
│ [SUCCESS] Time updated to: Day (08:30), Day 3      │
│ Custom Stats:                                       │
│   hunger: 80 → 79 (-1)                              │
│   thirst: 70 → 68 (-2)                              │
└─────────────────────────────────────────────────────┘
```

---

## Data Schemas

### 1. `character.json` — Character with Custom Stats

**New fields:**
- `speed_kmh` (optional, default: 4)
- `custom_stats` (optional)

```json
{
  "name": "Marked One",
  "race": "Human",
  "class": "Loner",
  "level": 1,
  "hp": {"current": 25, "max": 25},
  "gold": 450,
  "speed_kmh": 4,

  "custom_stats": {
    "hunger": {"current": 80, "max": 100},
    "thirst": {"current": 70, "max": 100},
    "radiation": {"current": 0, "max": 500},
    "sleep": {"current": 90, "max": 100}
  }
}
```

**Notes:**
- `speed_kmh` — character movement speed (km/h)
  - Default: 4 km/h (normal walking)
  - Can be changed: 2 km/h (stealth), 6 km/h (running), 8 km/h (mounted)
- `custom_stats` — any additional characteristics
  - `max: null` → no upper limit (for Civilization resources)
  - `min` defaults to 0 if not specified

---

### 2. `locations.json` — Locations with Distances

**New field in connections:** `distance_meters`

```json
{
  "Cordon": {
    "position": "southern border of the Zone",
    "connections": [
      {
        "to": "Junkyard",
        "path": "trail through fields, 2km north",
        "distance_meters": 2000
      },
      {
        "to": "100 Rads Bar",
        "path": "in the center of Cordon, 5 min walk",
        "distance_meters": 200
      }
    ],
    "description": "..."
  }
}
```

**Notes:**
- `distance_meters` — distance in meters between locations
- If not specified → time is not calculated automatically
- Connections are bidirectional (A→B and B→A should have same distance)

---

### 3. `campaign-overview.json` — Campaign Rules

**New fields:**
- `precise_time` (HH:MM for precise calculation)
- `campaign_rules.time_effects` (stat change rules)

```json
{
  "campaign_name": "S.T.A.L.K.E.R. — The Zone",
  "time_of_day": "Morning",
  "precise_time": "08:30",
  "current_date": "April 15, 2012",

  "campaign_rules": {
    "time_effects": {
      "enabled": true,

      "rules": [
        {
          "stat": "hunger",
          "per_hour": -2,
          "min": 0,
          "max": 100
        },
        {
          "stat": "thirst",
          "per_hour": -3,
          "min": 0,
          "max": 100
        },
        {
          "stat": "radiation",
          "per_hour": -1,
          "min": 0,
          "max": 500,
          "comment": "Natural radiation decay"
        }
      ],

      "stat_consequences": {
        "hunger_zero": {
          "condition": {
            "stat": "hunger",
            "operator": "<=",
            "value": 0
          },
          "effects": [
            {
              "type": "hp_damage",
              "amount": -1,
              "per_hour": true
            },
            {
              "type": "message",
              "text": "You are starving to death"
            }
          ]
        }
      }
    }
  }
}
```

**Notes:**
- `time_effects.enabled` — enable/disable auto-effects
- `rules` — stat changes per hour
- `stat_consequences` — what happens at critical values

---

### 4. `consequences.json` — Deferred Events

**New field:** `trigger_hours` (for automatic triggers)

```json
{
  "active": [
    {
      "id": "abc123",
      "consequence": "Trader arrives with news",
      "trigger": "in 24 hours",
      "trigger_hours": 24,
      "hours_elapsed": 0,
      "created": "2026-02-12T11:06:21+00:00"
    },
    {
      "id": "def456",
      "consequence": "Wolf approaches and offers work",
      "trigger": "when meeting at the Bar",
      "trigger_hours": null,
      "created": "2026-02-10T14:00:00+00:00"
    }
  ],
  "resolved": []
}
```

**Notes:**
- `trigger_hours != null` → automatic time trigger
- `trigger_hours == null` → event trigger (manual)
- `hours_elapsed` increases with each `dm-time.sh --elapsed X`

---

## Automatic Movement

### How it works:

1. **Claude calls:** `bash tools/dm-session.sh move "Junkyard"`
2. **System reads:**
   - `locations.json` → finds `distance_meters` in connection
   - `character.json` → reads `speed_kmh` (default: 4)
3. **System calculates:**
   ```
   distance_km = distance_meters / 1000
   elapsed_hours = distance_km / speed_kmh
   ```
4. **System updates:**
   - `precise_time` (08:00 → 08:30)
   - `time_of_day` (Morning → Day, if crossed 12:00)
5. **System applies:**
   - `time_effects` (hunger -2/h, thirst -3/h)
   - `stat_consequences` (if hunger = 0 → HP damage)
   - Checks `consequences` with `trigger_hours`

### Calculation Examples:

| Distance | Speed | Time |
|----------|-------|------|
| 200m | 4 km/h | 3 minutes (0.05h) |
| 1000m | 4 km/h | 15 minutes (0.25h) |
| 2000m | 4 km/h | 30 minutes (0.5h) |
| 5000m | 4 km/h | 1.25 hours |
| 2000m | 2 km/h (stealth) | 60 minutes (1h) |
| 2000m | 8 km/h (mounted) | 15 minutes (0.25h) |

### Speed Modifiers:

```json
{
  "speed_kmh": 4,  // Base walking
  "speed_kmh": 2,  // Stealth (×0.5)
  "speed_kmh": 6,  // Fast walking (×1.5)
  "speed_kmh": 8,  // Mounted/vehicle (×2)
}
```

---

## CLI Commands

### Movement (automatic time)

```bash
# Move to location (time calculated automatically)
bash tools/dm-session.sh move "Junkyard"

# Output:
# [SUCCESS] Party moved from Cordon to Junkyard
# [TIME] Travel time: 30 minutes (0.5 hours)
# [SUCCESS] Time updated to: Day (08:30), April 15, 2012
# Custom Stats:
#   hunger: 80 → 79 (-1)
#   thirst: 70 → 68 (-2)
```

### Custom stats (without character name)

```bash
# Show value (automatically for active character)
bash tools/dm-player.sh custom-stat hunger
# Output: hunger: 80/100

# Change value
bash tools/dm-player.sh custom-stat hunger +15
# Output: hunger: 80 → 95 (+15)

bash tools/dm-player.sh custom-stat thirst -10
# Output: thirst: 70 → 60 (-10)
```

### Manual time change (if needed)

```bash
# Option 1: Manual elapsed (Claude decides how much time passed)
bash tools/dm-time.sh "Evening" "April 15, 2012" --elapsed 4

# Option 2: Precise time (Python calculates difference)
bash tools/dm-time.sh "Noon" "April 15, 2012" --precise-time "12:30"
# (If was 08:00 → calculates 4.5 hours)
```

### Deferred events (with auto-triggers)

```bash
# Event with auto-trigger (in 24 hours)
bash tools/dm-consequence.sh add "Trader arrives" "in 24 hours" --hours 24

# Event without auto-trigger (manual)
bash tools/dm-consequence.sh add "Wolf offers work" "when meeting at the Bar"

# Check active events
bash tools/dm-consequence.sh check
```

### HP without character name

```bash
# Damage to active character
bash tools/dm-player.sh hp -5
# Output: DAMAGE Marked One took 5 damage!
#         HP: 20/25

# Heal active character
bash tools/dm-player.sh hp +8
# Output: HEAL Marked One healed 8 HP!
#         HP: 25/25
```

---

## Usage Examples

### Example 1: STALKER — Journey with Automatic Time

```bash
# Initial state
bash tools/dm-player.sh custom-stat hunger
# Output: hunger: 80/100

# Move from Cordon to Junkyard (2000m, 30 minutes)
bash tools/dm-session.sh move "Junkyard"

# Output:
# [SUCCESS] Party moved from Cordon to Junkyard
# [TIME] Travel time: 30 minutes (0.5 hours)
# [SUCCESS] Time updated to: Morning (08:30), April 15, 2012
# Custom Stats:
#   hunger: 80 → 79 (-1)    # -2/h * 0.5h = -1
#   thirst: 70 → 68 (-2)    # -3/h * 0.5h = -1.5 ≈ -2
#   radiation: 0 → 0 (0)
#   sleep: 90 → 90 (0)      # -1.5/h * 0.5h = -0.75 ≈ 0

# Player eats canned food
bash tools/dm-player.sh custom-stat hunger +20
# Output: hunger: 79 → 99 (+20)
```

---

### Example 2: STALKER — Hunger and Death

```bash
# Player forgot to eat for 50 hours (manual)
bash tools/dm-time.sh "Evening" "April 17, 2012" --elapsed 50

# Output:
# [SUCCESS] Time updated to: Evening, April 17, 2012
# Custom Stats:
#   hunger: 80 → 0 (-100, clamped to min)
#   thirst: 70 → 0 (-150, clamped to min)
# Stat Consequences:
#   ⚠️ hunger_zero: You are starving to death
#   ⚠️ thirst_zero: Dehydration is killing you
# HP: 25 → -125 (hunger -50HP, thirst -100HP)
# STATUS: DEAD
```

---

### Example 3: Deferred Events with Auto-Triggers

```bash
# Add event "Emission in 8 hours"
bash tools/dm-consequence.sh add "Emission hits location" "in 8 hours" --hours 8
# Output: [SUCCESS] Added timed consequence [abc123]: Emission (triggers in 8h)

# 5 hours pass (movement or manual)
bash tools/dm-time.sh "Evening" "Day 1" --elapsed 5
# (event NOT triggered, 3 hours remaining)

# Another 4 hours pass
bash tools/dm-time.sh "Night" "Day 1" --elapsed 4

# Output:
# [SUCCESS] Time updated to: Night, Day 1
# Triggered Events:
#   ⚠️ [abc123] Emission hits location
```

---

### Example 4: Changing Character Speed

```bash
# Character sneaking (×0.5 speed)
# Manually change in character.json: "speed_kmh": 2

bash tools/dm-session.sh move "Junkyard"
# Output:
# [TIME] Travel time: 60 minutes (1.0 hours)  # Instead of 30 minutes
# Custom Stats:
#   hunger: 80 → 78 (-2)  # -2/h * 1h = -2
#   thirst: 70 → 67 (-3)  # -3/h * 1h = -3

# Character on horseback (×2 speed)
# "speed_kmh": 8

bash tools/dm-session.sh move "Agroprom"  # 3000m
# Output:
# [TIME] Travel time: 22 minutes (0.375 hours)  # Instead of 45 minutes
```

---

## Backward Compatibility

### Guarantees:

1. **Standard D&D campaigns:**
   - If `custom_stats` is absent → ignored
   - If `time_effects.enabled = false` or absent → not applied
   - If `distance_meters` is absent → time not calculated
   - Everything works as before

2. **Existing consequences:**
   - If `trigger_hours` is absent → event-based (manual trigger)
   - Old consequences remain valid

3. **Commands with character name:**
   - Old format `dm-player.sh hp "Marked One" -5` still works
   - New format `dm-player.sh hp -5` (without name) — preferred

4. **Manual time management:**
   - `dm-time.sh "Evening" "Day 3"` without `--elapsed` → time changes without effects
   - `dm-time.sh "Evening" "Day 3" --elapsed 4` → with effects

---

## Technical Details

### Modified Files:

1. **lib/session_manager.py**
   - Method `move_party()`: added time calculation
   - Method `_calculate_travel_time()`: distance/speed formula
   - Method `_apply_travel_time()`: calls time_manager

2. **lib/player_manager.py**
   - All methods (`modify_hp`, `modify_gold`, `modify_custom_stat`, `get_player`): `name` parameter made optional
   - Method `_get_active_character_name()`: auto-detect active character

3. **tools/dm-player.sh**
   - Sections `hp`, `custom-stat`: name optional, format validation

4. **character.json**
   - Added field `speed_kmh` (default: 4)

5. **locations.json**
   - Added field `distance_meters` in connections

6. **campaign-overview.json**
   - Added field `precise_time` (HH:MM)
   - Added section `campaign_rules.time_effects`

---

## Known Limitations

1. **Short distances (<100m):**
   - Time rounded to minutes
   - Less than 1 minute → 0 hours → stats don't change
   - Solution: not critical for gameplay

2. **Auto-created connections:**
   - If connection created automatically (`"path": "traveled"`), it has no `distance_meters`
   - Solution: always create locations via `dm-location.sh connect` with distance specified

3. **Speed changes:**
   - Need to manually edit `character.json`
   - Solution: add command `dm-player.sh speed <value>` in future

---

## Coordinate System and Smart Navigation

### Implemented (v3.0):

#### 1. Coordinate System

Each location has coordinates `{x, y}` in meters:
- **Origin**: (0, 0) — campaign starting location
- **X-axis**: West (-) / East (+)
- **Y-axis**: South (-) / North (+)
- **Bearing**: Direction in degrees (0°=North, 90°=East, 180°=South, 270°=West)

```json
{
  "Cordon": {
    "coordinates": {"x": 0, "y": 0},
    "blocked_ranges": []
  }
}
```

#### 2. Connections with Distance and Bearing

```json
{
  "connections": [
    {
      "to": "Junkyard",
      "path": "trail through fields",
      "distance_meters": 2000,
      "bearing": 0,
      "terrain": "open"
    }
  ]
}
```

#### 3. Blocked Ranges

Angular ranges where direct path is impossible:

```json
{
  "blocked_ranges": [
    {
      "from": 290,
      "to": 320,
      "reason": "Radiation anomaly 'Funnel'"
    }
  ]
}
```

**Features:**
- Supports wrap-around (350° - 10° = range through 0°)
- Tolerance ±5° for checking close directions

#### 4. Path Preferences (DM Decision Caching)

System remembers DM's choice about route between locations:

```json
{
  "path_preferences": {
    "Cordon <-> Agroprom": {
      "decision": "direct",
      "decided_at": "2026-02-12T14:16:59Z"
    }
  }
}
```

**Decision types:**
- `direct` — use direct path
- `use_route` — use existing route through waypoints
- `blocked` — route is blocked

#### 5. Smart Pathfinding

During movement, system automatically:
1. Checks cached decision
2. If no decision — finds all possible routes (BFS)
3. Compares direct path vs existing routes
4. Requests DM decision (once)
5. Saves decision for future use

#### 6. ASCII Maps

**Full map:**
```bash
dm-map.sh [--width 80] [--height 40]
```

**Minimap (radius 5 cells):**
```bash
dm-map.sh --minimap [--radius 5]
```

Symbols:
- `@` — current player position
- `●` — location
- `─` / `│` — connections
- `▓` — fog of war (unexplored areas)

### New CLI Commands

#### Adding location with auto-coordinates:
```bash
dm-location.sh add "Bunker X-18" "underground complex" \
  --from "Agroprom" \
  --bearing 90 \
  --distance 2500 \
  --terrain underground
```

Automatically:
- Calculates coordinates
- Creates bidirectional connection
- Adds reverse bearing

#### Route management:
```bash
# View all possible routes
dm-location.sh routes "Cordon" "Agroprom"

# Interactive route choice (remembered)
dm-location.sh decide "Cordon" "Agroprom"
```

#### Blocking directions:
```bash
# Block range 290°-320°
dm-location.sh block "Cordon" 290 320 "Radiation anomaly"

# Unblock
dm-location.sh unblock "Cordon" 290 320
```

#### Maps:
```bash
# Full map
dm-map.sh

# Minimap (for navigation)
dm-map.sh --minimap

# Wide map
dm-map.sh --width 120 --height 50
```

### System Example

```bash
# 1. Add new location east of Agroprom
dm-location.sh add "Bunker" "to the east" --from "Agroprom" --bearing 90 --distance 2500
# [INFO] Calculated coordinates: {'x': -500, 'y': 2000}
# [INFO] Auto-created bidirectional connection

# 2. View possible routes
dm-location.sh routes "Cordon" "Bunker"
# DIRECT PATH: 2062m, bearing 346.0° (NNW)
# EXISTING ROUTES: Cordon → Junkyard → Agroprom → Bunker (7500m, 3 hops)

# 3. DM decides to use direct path
dm-location.sh decide "Cordon" "Bunker"
# [1] DIRECT PATH (2062m)
# [2] USE EXISTING ROUTE (7500m, 3 hops)
# [3] BLOCK THIS ROUTE
# Enter choice: 1
# [SUCCESS] Cached decision: use direct path

# 4. Next movement automatically uses direct path
dm-session.sh move "Bunker"
# [TIME] Travel time: 31 minutes (0.52 hours)
# Custom Stats:
#   hunger: 95 → 94 (-1)
#   thirst: 70 → 68 (-2)
```

### Algorithms

#### BFS Pathfinding (`lib/pathfinding.py`):
- Find shortest path through existing connections
- Account for distance_meters in total distance calculation
- Return up to 5 alternative routes

#### Coordinate Calculation:
```python
dx = distance * sin(bearing_radians)
dy = distance * cos(bearing_radians)
new_x = origin_x + dx
new_y = origin_y + dy
```

#### Direct Distance:
```python
distance = sqrt((x2 - x1)² + (y2 - y1)²)
```

#### Bearing Calculation:
```python
bearing = atan2(dx, dy)  # radians
degrees = bearing * 180 / π
if degrees < 0: degrees += 360
```

### Data Schemas (supplement)

#### locations.json:
```json
{
  "Location Name": {
    "position": "description",
    "coordinates": {"x": 0, "y": 0},
    "blocked_ranges": [
      {"from": 160, "to": 200, "reason": "Cliff"}
    ],
    "connections": [
      {
        "to": "Other Location",
        "path": "description",
        "distance_meters": 2000,
        "bearing": 45,
        "terrain": "open"
      }
    ],
    "description": "...",
    "discovered": "timestamp"
  }
}
```

#### campaign-overview.json:
```json
{
  "path_preferences": {
    "Location A <-> Location B": {
      "decision": "direct" | "use_route" | "blocked",
      "route": ["A", "Middle", "B"],
      "decided_at": "timestamp",
      "reason": "optional explanation"
    }
  }
}
```

---

---

## Location Diameter & Path-Based Terrain Visualization (v4.0)

**Status:** IMPLEMENTED
**Date:** 2026-02-12

### Overview

Each location now has a physical size (`diameter_meters`), and the system automatically detects when paths cross intermediate locations. GUI displays terrain-based regions precisely along paths between locations.

### 1. Location Diameter

**locations.json:**
```json
{
  "Agroprom": {
    "diameter_meters": 500,
    "coordinates": {"x": -3000, "y": 2000},
    "connections": [...]
  }
}
```

**Location sizes:**
- Small buildings: 10-50m (bar, bunker)
- Settlements: 100-200m (checkpoints, villages)
- Large territories: 300-500m (junkyards, complexes)

**GUI visualization:**
- Circles scale by `diameter_meters`
- Screen radius = `(diameter / 2) * zoom`
- Semi-transparent fill (alpha=100)
- Labels: `"Agroprom (500m)"`
- Hover detection uses real radius

### 2. Path Intersection Detection

**Module:** `lib/path_intersect.py`

**Algorithm:**
```python
def check_path_intersection(start, end, locations):
    """
    For each location between start and end:
      1. Calculate distance from center to line start→end
      2. If distance ≤ radius → path intersects location
      3. Return list of intersected locations
    """
```

**Functions:**
- `point_to_segment_distance()` - point↔line geometry
- `check_path_intersection()` - finds intersections
- `find_route_with_waypoints()` - builds route through waypoints

### 3. Automatic Path Splitting

**Module:** `lib/path_split.py`

**Problem:**
```
Agroprom ←3000m→ Junkyard  (path goes through Bunker X-18!)
```

**Solution:**
```
Agroprom ←2500m→ Bunker X-18 ←500m→ Junkyard
```

**Algorithm:**
1. Find all paths with intersections
2. For each intersected path:
   - Remove long path A↔C (bidirectional)
   - Create short paths A↔B, B↔C (if don't exist)
   - Preserve terrain type for all segments
3. **Duplicate check:** don't create if connection already exists

**CLI:**
```bash
# Preview changes
dm-location.sh split --dry-run

# Apply splitting
dm-location.sh split
```

**Example output:**
```
📍 Splitting: Agroprom → Junkyard
   Passes through: Bunker X-18
   ✗ Removed: Agroprom ↔ Junkyard (3000m)
   ✓ Added: Junkyard ↔ Bunker X-18 (500m, forest)
   ○ Keep existing: Agroprom ↔ Bunker X-18
```

### 4. Path-Based Terrain Visualization

**Problem with Voronoi (v3.0):**
- Colored background by **nearest connection point**
- Result: mixed colors, unclear boundaries
- From Agroprom to Bunker was open, but background showed forest

**New algorithm (v4.0):**
```python
def generate_terrain_background():
    """
    For each screen pixel:
      1. Convert screen → world coordinates
      2. Find nearest path LINE (not point!)
      3. Take terrain of that path
      4. Paint pixel in terrain color
    """
```

**Result:**
- Clear terrain corridors between locations
- Agroprom→Bunker: entire corridor **open** (green)
- Bunker→Junkyard: entire corridor **forest** (dark green)
- Cordon→Junkyard: entire corridor **open** (green)
- No mixed colors

**Terrain types:**
```python
TERRAIN_COLORS = {
    'open':     (100, 200, 100),  # Green
    'forest':   (50, 150, 50),    # Dark green
    'urban':    (150, 150, 150),  # Gray
    'water':    (50, 150, 255),   # Blue
    'mountain': (120, 120, 120),  # Dark gray
    'desert':   (255, 200, 100),  # Yellow
    'swamp':    (100, 120, 80),   # Swamp
}
```

### 5. CLI Tools

**dm-path.sh:**
```bash
# Check intersections of specific path
dm-path.sh check "Agroprom" "Junkyard"
# Output: ⚠️ Path intersects: Bunker X-18

# Build optimal route
dm-path.sh route "Cordon" "Agroprom"
# Output: 🗺️ Route: Cordon → Junkyard → Bunker X-18 → Agroprom

# Find all intersections in campaign
dm-path.sh analyze
# Output: List of all paths with intersections
```

**dm-location.sh split:**
```bash
# Preview without changes
dm-location.sh split --dry-run

# Apply path splitting
dm-location.sh split
```

### 6. GUI Features (map_gui.py)

**Visualization:**
- ✅ Procedural terrain background (path-based, not Voronoi)
- ✅ Locations scale by diameter_meters
- ✅ Only direct paths (no intersections)
- ✅ Auto-redraw on zoom/pan/reload (R key)
- ✅ Terrain legend with colored lines

**Controls:**
- Mouse wheel: Zoom
- LMB + Drag: Pan
- Click on location: Information
- R: Reload data
- ESC: Exit

**Launch:**
```bash
dm-map.sh --gui
```

### 7. Usage Examples

**Add location with diameter:**
```bash
dm-location.sh add "Rostok Factory" "east of Junkyard" \
  --from "Junkyard" --bearing 90 --distance 1500 \
  --terrain urban --diameter 250
```

**Check graph for intersections:**
```bash
dm-path.sh analyze
```

**Split long paths:**
```bash
dm-location.sh split
```

**Open GUI map:**
```bash
dm-map.sh --gui
```

### 8. Technical Details

**Files:**
- `lib/pathfinding.py` — A* pathfinding
- `lib/path_manager.py` — Navigation and route suggestion
- `lib/path_split.py` — Automatic long path splitting
- `lib/path_intersect.py` — Intersection detector
- `lib/map_renderer.py` — Path-based terrain rendering
- `lib/map_gui.py` — Pygame GUI
- `tools/dm-location.sh` — CLI for location management
- `tools/dm-path.sh` — CLI for graph analysis
- `tools/dm-map.sh` — CLI for maps (ASCII/GUI)

---

## v6.0 — Encounter System (Random Events)

### 1. Concept

**D&D-based random encounter system** for travel between locations. Instead of hardcoded events, uses:
- d20 roll to check avoiding encounter
- DC depends on distance (farther = more dangerous)
- Character modifier (stealth, awareness, etc.)
- Time of day (night is more dangerous)
- DM interpretation (not automatic events)

**Waypoint system:**
- When encounter occurs, creates temporary location mid-journey
- Player can only go forward or backward
- Waypoint deleted immediately after leaving
- Shown on map as orange triangles

### 2. Check Mechanics

#### DC Formula
```
DC = base_dc + (segment_km * distance_modifier) + time_modifier
Cap: DC ≤ 30
```

**Avoidance check:**
```
Roll: 1d20 + character_modifier
If roll < DC → Encounter triggered
```

**Path segmentation:**
| Distance | Segments | Checks |
|----------|----------|--------|
| < 1 km | 1 | 1 |
| 1-3 km | 1 | 1 |
| 3-6 km | 2 | 2 |
| 6+ km | 3 | 3 |

**Each segment** checked separately. DC calculated for **segment length**, not full distance.

#### Balance Settings (STALKER)
```json
{
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
    "Night": 4
  }
}
```

**Balance results:**
| Distance | DC | Checks | Chance (one) | Total |
|----------|----|---------:|------------:|-----:|
| 0.3 km | N/A | 0 | 0% | 0% (too short) |
| 0.5 km | 10 | 1 | 30% | 30% |
| 1 km | 12 | 1 | 40% | 40% |
| 2 km | 12 | 1 | 40% | 60% |
| 3 km | 14 | 2 | 50% | 75% |
| 5 km | 18 | 2 | 70% | 91% |
| 7 km | 17 | 3 | 65% | 96% |
| 10 km | 21 | 3 | 85% | 99.7% |

**Logic:**
- Short paths (<300m): safe, skipped
- Medium (1-3km): low DC, 30-60% chance
- Long (5+km): high DC, almost guaranteed encounters
- At night: +4 DC (much more dangerous)

### 3. Encounter Types

After encounter triggered, roll **d20 for encounter nature:**

| Roll | Category | Examples |
|------|----------|---------|
| 1-5 | Dangerous | Enemies, anomalies, traps |
| 6-10 | Neutral | Stalkers, traders, animals |
| 11-15 | Beneficial | Loot, information, help |
| 16-20 | Special | Unique events, artifacts |

**DM interprets result** based on:
- Location and terrain
- Time of day
- Current plot
- Character state

### 4. Waypoint System

#### When is waypoint created?
**Only for encounters requiring player decision:**
- Combat (fight)
- Social (conversation)
- Hazard (obstacle)

**Auto-resolve without waypoint:**
- Loot (finding)
- Flavor (atmosphere)

#### Waypoint structure
```json
{
  "waypoint_cordon_agroprom_seg1": {
    "is_waypoint": true,
    "original_journey": {
      "from": "Cordon",
      "to": "Agroprom",
      "segment": 1,
      "total_segments": 2,
      "progress_meters": 1250,
      "remaining_meters": 1250,
      "terrain": "forest"
    },
    "coordinates": {
      "x": 150,
      "y": 200
    },
    "diameter_meters": 10,
    "description": "You stopped mid-journey between Cordon and Agroprom",
    "connections": [
      {
        "to": "Cordon",
        "path": "go back",
        "distance_meters": 1250,
        "bearing": 180,
        "terrain": "forest"
      },
      {
        "to": "Agroprom",
        "path": "continue journey",
        "distance_meters": 1250,
        "bearing": 0,
        "terrain": "forest"
      }
    ]
  }
}
```

**Waypoint coordinates:**
```python
progress_ratio = distance_traveled / total_distance
waypoint_x = from_x + (to_x - from_x) * progress_ratio
waypoint_y = from_y + (to_y - from_y) * progress_ratio
```

#### Movement restrictions
From waypoint can ONLY go:
- Forward → continue to destination
- Back → return to start of path

Attempt to go elsewhere → `[ERROR] Cannot travel - only forward/back allowed`

#### Cleanup
Waypoint deleted **immediately** when player leaves (forward or back).

### 5. Visualization

**GUI map (dm-map.sh --gui):**
- Waypoint = orange triangle △
- Regular location = circle (color by type)
- Paths = straight lines (color by terrain)

**ASCII map (dm-map.sh):**
```
@ = Current position
△ = Waypoint
```

### 6. CLI Commands

```bash
# Enable/disable system
dm-encounter.sh toggle

# Status
dm-encounter.sh status

# Configure parameters
dm-encounter.sh set-base-dc 8
dm-encounter.sh set-distance-mod 4
dm-encounter.sh set-stat custom:awareness
dm-encounter.sh set-time-mod Night 4

# Manual check
dm-encounter.sh check "Cordon" "Agroprom" 2500 forest
```

### 7. Movement Integration

**session_manager.py:**
```python
def move_party(self, location):
    # Check: is this waypoint?
    if self.encounter_manager.is_waypoint(old_location):
        return self._handle_waypoint_movement(old_location, location)

    # Get path info
    route_info = self._get_route_info(old_location, location)
    distance_meters = route_info['distance_meters']
    terrain = route_info['terrain']

    # Check encounters if enabled
    if self.encounter_manager.is_enabled() and distance_meters > 0:
        journey = self.encounter_manager.check_journey(
            from_loc=old_location,
            to_loc=location,
            distance_meters=distance_meters,
            terrain=terrain
        )

        # Process each waypoint
        for waypoint in journey['waypoints']:
            if waypoint['encounter']:
                print(manager.format_journey_output(journey))

                # DM chooses type
                enc_type = input("Type [1=Combat,2=Social,3=Hazard,4=Loot,5=Flavor]: ")

                if enc_type in ['1','2','3']:  # Waypoint required
                    waypoint_name = manager.create_waypoint_location(...)
                    # Move to waypoint, apply time
                    self._update_location(waypoint_name)
                    self.time_manager.add_time_hours(waypoint['time_elapsed_min']/60)
                    # STOP journey
                    return {'status': 'waypoint', 'location': waypoint_name}
                else:  # Auto-resolve
                    description = input("DM: Describe... ")
                    print(f"\n{description}\n")
                    # Continue journey

        # If all encounters auto-resolved — final arrival
        self._update_location(location)
        self.time_manager.add_time_hours(journey['total_time_min']/60)
```

### 8. Edge Cases Tested

✅ **Test 1: Short distance (<300m)**
- 200m between locations → skipped, no checks

✅ **Test 2: Medium distance (1km)**
- 1 segment, 1 check

✅ **Test 3: Long distance (5km)**
- 2 segments, 2 checks

✅ **Test 4: Waypoint movement restriction**
- From waypoint can only forward/back
- Attempt to third location → error

✅ **Test 5: Auto-resolve encounter**
- Loot encounter → auto-resolve, no waypoint

✅ **Test 6: Multiple encounters**
- 7km path → 3 segments → 2 encounters triggered

✅ **Test 7: Waypoint cleanup**
- Waypoint deleted when leaving

### 9. Technical Details

**Files:**
- `lib/path_intersect.py` - Detection algorithms
- `lib/path_split.py` - Automatic splitting
- `lib/map_gui.py` - Pygame GUI with terrain
- `tools/dm-path.sh` - CLI for paths
- `tools/dm-location.sh split` - CLI for splitting

**Dependencies:**
- `pygame` (for GUI)
- `math` (geometry)

**Performance:**
- Path-based terrain: ~5-10ms background generation
- Sample step: 5 pixels (5x5 blocks)
- Caching: background regenerated only on zoom/pan/reload

### 9. Roadmap

#### Implemented ✅:
- [x] Location diameters
- [x] Path intersection detection
- [x] Automatic path splitting (no duplicates)
- [x] Path-based terrain visualization
- [x] GUI map with scaled locations
- [x] CLI tools for analysis and splitting

#### Future improvements:
- [ ] Speed modifiers by terrain (forest = ×1.5 time)
- [ ] Random encounter checks during movement
- [ ] Waypoints on long paths (rest points)
- [ ] Terrain elevation for 3D-like visualization
- [ ] Weather effects on terrain (rain slows open, easier in forest)

---

## GUI Map — Interactive Visualization (v5.0)

### What was added:

#### 1. Pygame GUI with Path-Based Terrain
- **Terrain colored by path type** (not by location) — green/yellow/blue corridors along roads
- **Fog of war** — everything beyond 1km from paths is black
- **Static generation** — background drawn once (30 sec), then 60 FPS
- **7 terrain types:** open, forest, urban, water, mountain, desert, swamp

#### 2. Scaled Locations
- **Location diameter** (`diameter_meters` in JSON) — Cordon 100m, Junkyard 300m
- Circles scale with zoom
- Current position — red, others — blue

#### 3. Controls
- **Zoom:** Mouse wheel (0.1x - 5.0x)
- **Pan:** LMB drag
- **Select:** Click on location
- **Reload:** R key

#### 4. Launch
```bash
uv run python lib/map_gui.py
# or
bash tools/dm-map.sh --gui
```

---

## Appendix: Campaign Templates

### STALKER Campaign Template

**Note:** This template uses Russian for thematic flavor. Campaign data can be in any language.

**File:** `stalker-campaign-template.json`

```json
{
  "campaign_name": "S.T.A.L.K.E.R. — Зона",
  "genre": "Post-Apocalyptic Survival",
  "tone": {
    "horror": 70,
    "comedy": 10,
    "drama": 20
  },
  "setting": "Зона Отчуждения",
  "magic_level": "Отсутствует",
  "setting_type": "Post-Apocalyptic",
  "current_date": "15 апреля 2012",
  "time_of_day": "Утро",
  "precise_time": "08:00",
  "player_position": {
    "current_location": "Кордон",
    "previous_location": null,
    "arrival_time": null
  },
  "current_character": null,
  "session_count": 0,

  "campaign_rules": {
    "tone_guide": "Мрачная атмосфера выживания. Каждый выход может быть последним. Зона не прощает ошибок. Чёрный юмор редкий, как артефакт в аномалии.",

    "time_effects": {
      "enabled": true,

      "rules": [
        {
          "stat": "hunger",
          "per_hour": -2,
          "min": 0,
          "max": 100,
          "comment": "Голод увеличивается постоянно"
        },
        {
          "stat": "thirst",
          "per_hour": -3,
          "min": 0,
          "max": 100,
          "comment": "Жажда критичнее голода"
        },
        {
          "stat": "radiation",
          "per_hour": -1,
          "min": 0,
          "max": 500,
          "comment": "Естественный распад радиации"
        },
        {
          "stat": "sleep",
          "per_hour": -1.5,
          "min": 0,
          "max": 100,
          "comment": "Усталость накапливается"
        }
      ],

      "stat_consequences": {
        "hunger_zero": {
          "condition": {
            "stat": "hunger",
            "operator": "<=",
            "value": 0
          },
          "effects": [
            {
              "type": "hp_damage",
              "amount": -1,
              "per_hour": true
            },
            {
              "type": "message",
              "text": "Ты умираешь от голода. Желудок свело судорогой."
            }
          ]
        },
        "thirst_zero": {
          "condition": {
            "stat": "thirst",
            "operator": "<=",
            "value": 0
          },
          "effects": [
            {
              "type": "hp_damage",
              "amount": -2,
              "per_hour": true
            },
            {
              "type": "message",
              "text": "Обезвоживание убивает тебя. Язык распух, губы потрескались."
            }
          ]
        },
        "radiation_high": {
          "condition": {
            "stat": "radiation",
            "operator": ">=",
            "value": 200
          },
          "effects": [
            {
              "type": "hp_damage",
              "amount": -1,
              "per_hour": true
            },
            {
              "type": "condition",
              "name": "Лучевая болезнь"
            },
            {
              "type": "message",
              "text": "Дозиметр пищит не переставая. Радиация жрёт тебя изнутри."
            }
          ]
        },
        "radiation_critical": {
          "condition": {
            "stat": "radiation",
            "operator": ">=",
            "value": 300
          },
          "effects": [
            {
              "type": "hp_damage",
              "amount": -3,
              "per_hour": true
            },
            {
              "type": "condition",
              "name": "Лучевая болезнь (критическая)"
            },
            {
              "type": "message",
              "text": "Дозиметр орёт как ненормальный. Тебе пиздец."
            }
          ]
        },
        "sleep_zero": {
          "condition": {
            "stat": "sleep",
            "operator": "<=",
            "value": 0
          },
          "effects": [
            {
              "type": "condition",
              "name": "Истощение"
            },
            {
              "type": "message",
              "text": "Ты еле держишься на ногах. Глаза слипаются."
            }
          ]
        }
      }
    }
  }
}
```

---

### STALKER Character Template

**Note:** This template uses Russian for thematic flavor. Campaign data can be in any language.

**File:** `stalker-character-template.json`

```json
{
  "name": "Сталкер Мечёный",
  "race": "Человек",
  "class": "Одиночка",
  "level": 1,
  "hp": {
    "current": 25,
    "max": 25
  },
  "ac": 14,
  "gold": 450,

  "stats": {
    "str": 12,
    "dex": 14,
    "con": 13,
    "int": 10,
    "wis": 12,
    "cha": 9
  },

  "saves": {
    "str": 1,
    "dex": 2,
    "con": 1,
    "int": 0,
    "wis": 1,
    "cha": -1
  },

  "skills": {
    "perception": 3,
    "survival": 3,
    "stealth": 4,
    "investigation": 2
  },

  "custom_stats": {
    "hunger": {
      "current": 80,
      "max": 100,
      "min": 0
    },
    "thirst": {
      "current": 70,
      "max": 100,
      "min": 0
    },
    "radiation": {
      "current": 0,
      "max": 500,
      "min": 0
    },
    "sleep": {
      "current": 90,
      "max": 100,
      "min": 0
    }
  },

  "equipment": [
    "ПМ (9x18mm, 8 патронов)",
    "Кожанка (AC 12)",
    "Детектор аномалий «Эхо»",
    "ПДА",
    "Болты (20 шт)",
    "Консервы (3 банки)",
    "Вода (2 бутылки)",
    "Аптечка",
    "Антирад (2 шт)"
  ],

  "features": [
    "Чувство опасности (преимущество на Perception в Зоне)",
    "Выживальщик (преимущество на Survival)"
  ],

  "hit_dice": "1d8",
  "background": "Сталкер",
  "alignment": "Нейтральный",
  "bonds": "Ищу пропавшего брата где-то в Зоне",
  "flaws": "Слишком доверяю своим чувствам",
  "ideals": "Свобода — Зона принадлежит всем",
  "traits": "Всегда проверяю болтами аномалии. Всегда.",
  "notes": [],
  "conditions": [],
  "xp": {
    "current": 0,
    "next_level": 300
  },
  "current_location": "Кордон"
}
```

---

### Civilization Campaign Template

**Note:** This template uses Russian for thematic flavor. Campaign data can be in any language.

**File:** `civilization-campaign-template.json`

```json
{
  "campaign_name": "Бессмертный Правитель — Цивилизация",
  "genre": "Civilization Builder",
  "tone": {
    "horror": 5,
    "comedy": 30,
    "drama": 65
  },
  "setting": "От каменного века до космоса",
  "magic_level": "Редкая",
  "setting_type": "Epic Strategy",
  "current_date": "Год 1, Поколение 1",
  "time_of_day": "Эпоха: Каменный Век",
  "precise_time": null,
  "player_position": {
    "current_location": "Племенная Пещера",
    "previous_location": null,
    "arrival_time": null
  },
  "current_character": null,
  "session_count": 0,

  "campaign_rules": {
    "tone_guide": "Эпический масштаб с человеческими историями. Каждое решение имеет последствия через поколения. Чёрный юмор (чума выкосила 40% населения, зато жильё подешевело). Советники сменяются, но правитель вечен.",

    "time_effects": {
      "enabled": true,

      "rules": [
        {
          "stat": "food",
          "per_hour": -5,
          "min": 0,
          "max": null,
          "comment": "Население ест постоянно (1 час = 1 поколение)"
        },
        {
          "stat": "population_growth",
          "per_hour": 0.1,
          "min": -100,
          "max": 100,
          "comment": "Естественный прирост населения"
        }
      ],

      "stat_consequences": {
        "starvation": {
          "condition": {
            "stat": "food",
            "operator": "<=",
            "value": 0
          },
          "effects": [
            {
              "type": "message",
              "text": "Голод косит твой народ. Люди умирают тысячами."
            }
          ]
        },
        "prosperity": {
          "condition": {
            "stat": "food",
            "operator": ">=",
            "value": 500
          },
          "effects": [
            {
              "type": "message",
              "text": "Изобилие пищи — народ растёт и процветает!"
            }
          ]
        }
      }
    }
  }
}
```

---

### Civilization Character Template

**Note:** This template uses Russian for thematic flavor. Campaign data can be in any language.

**File:** `civilization-character-template.json`

```json
{
  "name": "Бессмертный Правитель Ксар",
  "race": "Бессмертный",
  "class": "Правитель",
  "level": 1,
  "hp": {
    "current": 50,
    "max": 50
  },
  "ac": 15,
  "gold": 0,

  "stats": {
    "str": 10,
    "dex": 10,
    "con": 18,
    "int": 16,
    "wis": 14,
    "cha": 15
  },

  "custom_stats": {
    "population": {
      "current": 50,
      "max": null,
      "min": 0
    },
    "food": {
      "current": 100,
      "max": null,
      "min": 0
    },
    "materials": {
      "current": 30,
      "max": null,
      "min": 0
    },
    "knowledge": {
      "current": 5,
      "max": null,
      "min": 0
    },
    "faith": {
      "current": 10,
      "max": null,
      "min": 0
    },
    "culture": {
      "current": 8,
      "max": null,
      "min": 0
    },
    "population_growth": {
      "current": 0,
      "max": 100,
      "min": -100
    }
  },

  "equipment": [
    "Каменный жезл правителя",
    "Шкура волка",
    "Кремниевый нож"
  ],

  "features": [
    "Бессмертие (не умирает от старости)",
    "Божественная воля (народ обожествляет правителя)",
    "Вечная память (помнит все эпохи)"
  ],

  "background": "Бессмертный Правитель",
  "alignment": "Lawful Neutral",
  "bonds": "Мой народ — моя семья. Все они мои дети.",
  "flaws": "Иногда забываю, что смертные живут недолго",
  "ideals": "Прогресс — единственный путь к выживанию",
  "traits": "Говорю медленно и вдумчиво. Видел слишком много.",
  "notes": [],
  "conditions": [],
  "xp": {
    "current": 0,
    "next_level": 1000
  },
  "current_location": "Племенная Пещера"
}
```

---

**Date created:** 2026-02-12
**Last updated:** 2026-02-12 (v5.0 - GUI Map)
**Version:** 5.0 (Pygame GUI, Path-Based Terrain, Fog of War)
**Status:** Production Ready
