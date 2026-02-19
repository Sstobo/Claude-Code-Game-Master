# World Travel Module — DM Rules

Unified rules for coordinate navigation and automatic encounter checks during overland travel.

---

## ⚠️ MANDATORY: Location Creation Protocol

**EVERY time you add a location, you MUST use `--from/--bearing/--distance` flags.**
**NO EXCEPTIONS. Never call `dm-location.sh add` without coordinates.**

### Starting location (origin only)
The very first location of a campaign has no `--from`. Set coordinates manually in JSON:
```json
{"coordinates": {"x": 0, "y": 0}}
```

### Every subsequent location — ALWAYS use flags:
```bash
bash tools/dm-location.sh add "Location Name" "short description" \
  --from "Existing Location" \
  --bearing <0-359> \
  --distance <meters> \
  --terrain <space|road|asteroid|nebula|station|void>
```

**If you skip `--from/--bearing/--distance` → coordinates won't be set → map breaks → you failed.**

### Bearings reference
- 0° = north / up on map
- 90° = east / right
- 180° = south / down
- 270° = west / left

---

## Part 1: Navigation

### Coordinate System

**Origin:** `(0, 0)` at campaign starting location
**Axes:**
- X-axis: West (negative) / East (positive)
- Y-axis: South (negative) / North (positive)
- Units: meters

**Bearing:**
- 0° = North, 90° = East, 180° = South, 270° = West

### Adding Locations with Coordinates

```bash
bash tools/dm-location.sh add "Abandoned Farm" "Ruined homestead" \
  --from "Starting Village" \
  --bearing 90 \
  --distance 2500 \
  --terrain farmland
```

Module auto-calculates coordinates, creates bidirectional connection with `distance_meters`, bearing, and terrain metadata.

### Moving the Party

```bash
bash tools/dm-session.sh move "Temple"
bash tools/dm-session.sh move "Temple" --speed-multiplier 1.5
```

After move: distance/time is calculated, clock advances (via survival-stats if active), encounter check fires automatically.

### Route Decisions

When no direct connection exists between locations, the DM must decide the route:

```bash
bash .claude/modules/world-travel/tools/dm-navigation.sh decide "Village" "Temple"
```

**Options:**
1. **DIRECT PATH** — straight line (may cross impassable terrain)
2. **USE EXISTING ROUTE** — follow established connections
3. **BLOCK THIS ROUTE** — permanently mark inaccessible

Decision is cached in `path_preferences`. System never asks again for the same pair.

### Direction Blocking

Prevent movement in angular ranges (cliffs, radiation zones, walls):

```bash
bash .claude/modules/world-travel/tools/dm-navigation.sh block "Cliff Edge" 160 200 "Steep cliff drop"
bash .claude/modules/world-travel/tools/dm-navigation.sh unblock "Cliff Edge" 160 200
```

### Map Visualization

```bash
bash .claude/modules/world-travel/tools/dm-map.sh             # Full ASCII map
bash .claude/modules/world-travel/tools/dm-map.sh --color     # Colored ASCII map
bash .claude/modules/world-travel/tools/dm-map.sh --minimap   # Nearby locations only
bash .claude/modules/world-travel/tools/dm-map.sh --gui       # Interactive Pygame map
```

**Map symbols:** `@` = current location, `•` = other locations, `──` = connections

### Location Schema

```json
{
  "Agroprom": {
    "coordinates": {"x": -1000, "y": 3000},
    "connections": [
      {"to": "Junkyard", "distance_meters": 2000, "bearing": 135, "terrain": "road"}
    ],
    "blocked_ranges": [
      {"from": 270, "to": 310, "reason": "Radiation zone"}
    ]
  }
}
```

### When Coordinates Are Useful

**Use coordinates for:**
- Open-world exploration (STALKER, Fallout-style)
- Hex-based or grid campaigns
- Tactical positioning with realistic distances
- Visual map representation

**Skip coordinates for:**
- Linear dungeon crawls
- Abstract locations ("The Dreamrealm")
- Theater-of-the-mind style

---

## Part 2: Random Encounters

Encounter checks fire automatically after every `move` (via middleware). Manual check is also available.

### Activation Check

At session start, verify `campaign_rules.encounter_system.enabled = true`.
If yes, these rules are active for the session.

### Automatic vs Manual

**Automatic:** middleware intercepts `dm-session.sh move`, calls `dm-encounter.sh check` after navigation completes.

**Manual:**
```bash
bash .claude/modules/world-travel/tools/dm-encounter.sh check "<from>" "<to>" <distance_meters> [terrain]
```

Example:
```bash
bash .claude/modules/world-travel/tools/dm-encounter.sh check "Village" "Ruins" 2000 open
```

### How Encounters Work

1. System calculates number of segments (1–3 based on distance)
2. Each segment: roll d20 + character modifier vs DC
3. If roll < DC → encounter triggered
4. Nature roll determines category (Dangerous, Neutral, Beneficial, Special)
5. DM decides encounter type, creates waypoint if needed

### Encounter Types

| Type | Creates Waypoint? | DM Action |
|------|-------------------|-----------|
| **Combat** | Yes | Describe enemies, initiate combat |
| **Social** | Yes | Describe NPC encounter, handle dialogue |
| **Hazard** | Yes | Describe obstacle (anomaly, trap, weather) |
| **Loot** | No | Describe find, add items |
| **Flavor** | No | Atmospheric event, continue |

### Waypoints

When Combat/Social/Hazard triggers, system creates a temporary location mid-journey.

**Player options:**
- **Forward** — continue to destination (remaining distance)
- **Back** — return to origin (distance traveled so far)

System auto-creates waypoint location with coordinates and connections, removes it after player leaves.

### Configuration

```bash
bash .claude/modules/world-travel/tools/dm-encounter.sh toggle           # Enable/disable
bash .claude/modules/world-travel/tools/dm-encounter.sh set-base-dc 12   # Lower = more encounters
bash .claude/modules/world-travel/tools/dm-encounter.sh set-distance-mod 3
bash .claude/modules/world-travel/tools/dm-encounter.sh set-stat dex
bash .claude/modules/world-travel/tools/dm-encounter.sh set-stat stealth
bash .claude/modules/world-travel/tools/dm-encounter.sh set-stat custom:awareness
bash .claude/modules/world-travel/tools/dm-encounter.sh set-time-mod Night 4
bash .claude/modules/world-travel/tools/dm-encounter.sh status
```

### DC Formula

`DC = base_dc + (segment_km × distance_modifier) + time_modifier`

- Roll d20 + modifier **must meet or exceed DC** to avoid encounter
- Longer distance → higher DC → harder to avoid
- Max DC: 30

### When NOT to Check

- `encounter_system.enabled = false`
- Distance < `min_distance_meters` (default 300m)
- Teleportation or instant travel
- Movement within same building/area
- Do NOT duplicate encounter check if middleware already ran it

---

## Part 3: Vehicle System (Ships, Cities, Transports)

Vehicles are **dual-map locations**: an anchor on the global map + internal rooms on the local map.
Works for ships, cities, trains, dungeons — anything with an "inside".

### Creating a vehicle

```bash
# 1. Anchor location must already exist as a regular location
# 2. Register vehicle on it
bash .claude/modules/world-travel/tools/dm-vehicle.sh create "Indomitable" "starship" "Sigma Spaceport"
#   args: <vehicle_id> <vehicle_type> <anchor_location>

# 3. Add rooms (--from = anchor or another room)
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room indomitable "Bridge" --from "Indomitable" --bearing 0 --distance 50
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room indomitable "Engine Room" --from "Bridge" --bearing 180 --distance 80
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room indomitable "Quarters" --from "Bridge" --bearing 90 --distance 30
```

### Cities and stationary locations

A city is the same vehicle — it just doesn't move. Add `stationary: true` to `_vehicle` in locations.json:

```json
"Novosibirsk": {
  "coordinates": {"x": 0, "y": 0},
  "_vehicle": {
    "vehicle_id": "novosibirsk",
    "is_vehicle_anchor": true,
    "vehicle_type": "city",
    "dock_room": "Central Market",
    "proximity_radius_meters": 500,
    "stationary": true
  }
}
```

`stationary: true` — `move` returns an error, can't accidentally relocate a city.

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh create "Novosibirsk" "city" "Steppe Road"
# then manually add "stationary": true to locations.json
```

### Boarding / entering a location

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh board indomitable             # → dock_room
bash .claude/modules/world-travel/tools/dm-vehicle.sh board indomitable --room "Engine Room"  # → specific room
```

After boarding: `player_position.map_context = "local"`, `vehicle_id = "indomitable"`.

### Moving between rooms

When player is inside, regular move is intercepted automatically:

```bash
bash tools/dm-session.sh move "Engine Room"   # middleware sees local context → move-internal
```

**Encounters and time do NOT tick** for internal movement — it's a room transition, not travel.

### Exiting to global map

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh exit
# → player_position.current_location = anchor, map_context = "global"
```

### Moving the vehicle

```bash
# To an existing location (copies its coordinates)
bash .claude/modules/world-travel/tools/dm-vehicle.sh move indomitable "Mantisk-7 Station"

# To arbitrary coordinates
bash .claude/modules/world-travel/tools/dm-vehicle.sh move indomitable --x 5000 --y 3200
```

**What happens on move:**
1. Anchor gets new coordinates
2. All rooms shift by the same delta
3. Old external connections removed
4. New ones built by proximity_radius (terrain="docking")
5. Player inside → travels with ship (`player_status: "inside"`)
6. Player outside → stays put (`player_status: "outside"`, warn the player)

### Switching between vehicles

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh exit        # exit ship A
bash tools/dm-session.sh move "Ship B"                            # walk to ship B anchor
bash .claude/modules/world-travel/tools/dm-vehicle.sh board shipb # board ship B
bash .claude/modules/world-travel/tools/dm-vehicle.sh move shipb "Alpha Centauri"  # fly on B
```

### Status and map

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh status indomitable  # specific vehicle
bash .claude/modules/world-travel/tools/dm-vehicle.sh status              # all vehicles
bash .claude/modules/world-travel/tools/dm-vehicle.sh list                # list
bash .claude/modules/world-travel/tools/dm-vehicle.sh map indomitable     # ASCII internal map
```

### Data schema

**locations.json — anchor:**
```json
"Indomitable": {
  "coordinates": {"x": 1500, "y": 3200},
  "connections": [],
  "_vehicle": {
    "vehicle_id": "indomitable",
    "is_vehicle_anchor": true,
    "vehicle_type": "starship",
    "dock_room": "Bridge",
    "proximity_radius_meters": 5000,
    "stationary": false
  }
}
```

**locations.json — room:**
```json
"Bridge": {
  "coordinates": {"x": 0, "y": 30},
  "connections": [{"to": "Engine Room", "distance_meters": 80, "bearing": 180, "terrain": "internal"}],
  "_vehicle": {"vehicle_id": "indomitable", "is_vehicle_anchor": false, "map_context": "local"}
}
```

**campaign-overview.json — player position:**
```json
"player_position": {
  "current_location": "Bridge",
  "map_context": "local",
  "vehicle_id": "indomitable"
}
```

---

### campaign-overview.json Schema

```json
{
  "campaign_rules": {
    "encounter_system": {
      "enabled": true,
      "min_distance_meters": 300,
      "base_dc": 16,
      "distance_modifier": 2,
      "stat_to_use": "stealth",
      "use_luck": false,
      "time_dc_modifiers": {
        "Morning": 0,
        "Day": 0,
        "Evening": 2,
        "Night": 4
      }
    }
  }
}
```
