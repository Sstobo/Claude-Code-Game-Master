# World Travel — DM Rules

---

## Part 1: Navigation

### Moving the Party

```bash
bash tools/dm-session.sh move "Temple"
bash tools/dm-session.sh move "Temple" --speed-multiplier 1.5
```

After move: distance/time calculated, clock advances, encounter check fires automatically.

### Route Decisions

When no direct connection exists:

```bash
bash .claude/modules/world-travel/tools/dm-navigation.sh decide "Village" "Temple"
```

Options: **DIRECT PATH** / **USE EXISTING ROUTE** / **BLOCK THIS ROUTE**
Decision cached — system never asks again for the same pair.

### Direction Blocking

```bash
bash .claude/modules/world-travel/tools/dm-navigation.sh block "Cliff Edge" 160 200 "Steep cliff drop"
bash .claude/modules/world-travel/tools/dm-navigation.sh unblock "Cliff Edge" 160 200
```

### Map

```bash
bash .claude/modules/world-travel/tools/dm-map.sh             # Full ASCII map
bash .claude/modules/world-travel/tools/dm-map.sh --minimap   # Nearby only
bash .claude/modules/world-travel/tools/dm-map.sh --gui       # Interactive Pygame
```

---

## Part 2: Random Encounters

Fires automatically after every `move`. Manual check:

```bash
bash .claude/modules/world-travel/tools/dm-encounter.sh check "Village" "Ruins" 2000 open
```

### Encounter Types

| Type | Waypoint? | DM Action |
|------|-----------|-----------|
| Combat | Yes | Describe enemies, initiate combat |
| Social | Yes | NPC encounter, handle dialogue |
| Hazard | Yes | Obstacle (anomaly, trap, weather) |
| Loot | No | Describe find, add items |
| Flavor | No | Atmospheric event, continue |

### Waypoints

On Combat/Social/Hazard: temporary location created mid-journey.
Player options: **Forward** (continue) or **Back** (return to origin).
Waypoint removed after player leaves.

### DC Formula

`DC = base_dc + (segment_km × distance_modifier) + time_modifier`

Roll d20 + modifier must meet or exceed DC to avoid encounter. Max DC: 30.

### When NOT to Check

- `encounter_system.enabled = false`
- Distance < `min_distance_meters` (default 300m)
- Teleportation or instant travel
- Movement within same building/area
- Middleware already ran it — don't duplicate

---

## Part 3: Vehicles

### Creating a Vehicle (Ship Setup)

```bash
# 1. Register vehicle at an existing anchor location
bash .claude/modules/world-travel/tools/dm-vehicle.sh create kestrel spacecraft "Станция Кестрел"

# 2. First room: --from = anchor location name (NOT "Entrance" or anything else)
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room kestrel "Мостик" --from "Станция Кестрел" --bearing 90 --distance 10

# 3. Subsequent rooms: --from = existing room name
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room kestrel "Реакторный отсек" --from "Мостик" --bearing 270 --distance 8
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room kestrel "Двигатели" --from "Реакторный отсек" --bearing 270 --distance 10
```

**Rules:**
- `add-room` creates bidirectional connections automatically — do NOT use `dm-location.sh connect` after
- `dm-location.sh connect` requires 4 args: `connect "A" "B" "path_name" --terrain X --distance N`
- `dm-vehicle.sh map` shows only outgoing links from anchor — bidirectional data is correct even if display looks one-sided

### Boarding / Entering

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh board indomitable
bash .claude/modules/world-travel/tools/dm-vehicle.sh board indomitable --room "Engine Room"
```

### Moving Between Rooms

When player is inside, regular move is intercepted automatically — no encounters, no time tick.

```bash
bash tools/dm-session.sh move "Engine Room"
```

### Exiting to Global Map

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh exit
```

### Moving the Vehicle

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh move indomitable "Mantisk-7 Station"
bash .claude/modules/world-travel/tools/dm-vehicle.sh move indomitable --x 5000 --y 3200
```

Player inside → travels with vehicle. Player outside → stays put (system warns).

### Status

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh status
bash .claude/modules/world-travel/tools/dm-vehicle.sh map indomitable
```
