# World Travel Module — DM Rules

Unified rules for coordinate navigation and automatic encounter checks during overland travel.

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
