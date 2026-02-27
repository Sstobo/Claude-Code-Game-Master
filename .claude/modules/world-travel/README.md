# world-travel

**Module for the Claude Code DM System** | Navigation + Random Encounters | v1.0.0

---

Vanilla CORE tracks locations as named entries with a description. Moving the party
means writing a location name to JSON. That is the entire travel system.

`world-travel` replaces that with coordinate-based navigation, automatic pathfinding,
direction blocking, distance-accurate time calculation, and encounter checks that fire
on every move — all without touching CORE.

---

## What CORE does vs what this module adds

| Behavior | CORE (vanilla) | world-travel |
|---|---|---|
| `dm-session.sh move <loc>` | Writes location name to JSON | Calculates distance + time, advances clock, then triggers encounter check |
| `dm-location.sh add` | Saves name + description | Also computes (x, y) from bearing + distance, creates bidirectional connection |
| Location data | `{ "name": "...", "description": "..." }` | Plus `coordinates`, `connections[]` with distance/terrain/bearing, `blocked_ranges[]` |
| Travel time | Not tracked | Characters have `speed_kmh`; elapsed hours calculated per move |
| Random encounters | Nothing | Segmented DC check per journey, waypoint creation on trigger |
| Map | Nothing | ASCII render + Pygame GUI |

---

## Features

### Coordinate system

Every location stores `{ "x": N, "y": N }` in meters. When you add a location via
`dm-location.sh add --from <origin> --bearing <deg> --distance <m>`, the module
calculates coordinates automatically.

```bash
bash tools/dm-location.sh add "Old Mill" "east of the village" \
  --from "Village" --bearing 90 --distance 800 --terrain forest
# [INFO] Calculated coordinates: {"x": 800, "y": 0}
# [INFO] Direction from Village: East (E)
# [SUCCESS] Added location: Old Mill (east of the village)
```

The connection is created bidirectionally with distance, bearing, and terrain stored.

---

### BFS pathfinding and route decisions

Find the shortest route through the connection graph:

```bash
bash tools/dm-navigation.sh route "Village" "Ruins"
# Route: Village → Old Mill → Forest Path → Ruins
# Distance: 3400m, Hops: 3
```

When the same pair of locations is requested repeatedly, use `decide` to lock in a
preferred route. The decision is cached in `campaign-overview.json` under
`path_preferences` and reused on subsequent calls:

```bash
bash tools/dm-navigation.sh decide "Village" "Ruins"
# ROUTE DECISION: Village → Ruins
# [1] DIRECT PATH — 2100m, bearing 135°
# [2] USE EXISTING ROUTE — Village → Old Mill → Ruins, 3400m, 2 hops
# [3] BLOCK THIS ROUTE (permanently)
# Enter choice [1-3]:
```

To see all available routes without committing:

```bash
bash tools/dm-navigation.sh routes "Village" "Ruins"
```

---

### Direction blocking

Block a bearing arc at a location to represent terrain obstacles. The block is stored
in `locations.json` under `blocked_ranges` and checked by pathfinding when evaluating
direct paths:

```bash
bash tools/dm-navigation.sh block "Cliffside Camp" 160 200 "sheer drop"
# [SUCCESS] Blocked 160° - 200° at Cliffside Camp: sheer drop

bash tools/dm-navigation.sh unblock "Cliffside Camp" 160 200
```

Blocked arcs handle wrap-around correctly (e.g., 350° to 10° blocks through North).

---

### Move with time calculation

`dm-navigation.sh move` reads `speed_kmh` from `character.json` (default 4.0 km/h),
calculates elapsed hours from the connection's `distance_meters`, and advances the
campaign clock. If the `survival-stats` module is present, it delegates clock
advancement there; otherwise it prints elapsed time directly.

```bash
bash tools/dm-navigation.sh move "Old Mill"
# [INFO] Travel time: 0.20 hours (800m)
# [SUCCESS] Moved to: Old Mill

bash tools/dm-navigation.sh move "Old Mill" --speed-multiplier 2.0
# Useful for mounted travel, vehicles, sprinting
```

The `dm-session.sh` middleware intercepts `move` automatically, so the DM does not
need to call `dm-navigation.sh` directly — CORE's `dm-session.sh move <loc>` triggers
the full navigation pipeline.

---

### Path intersection detection

Check whether a straight line between two locations passes through known intermediate
locations (useful when adding cross-country connections):

```bash
bash tools/dm-navigation.sh path check "Village" "Ruins"
# Path intersects:
#   • Old Mill
#   • Forest Path
# Suggested: Village → Old Mill → Forest Path → Ruins

bash tools/dm-navigation.sh path analyze
# Scans all connections in locations.json for intersections
```

---

### Random encounter system

After every `move`, the middleware runs an encounter check. The journey is divided
into 1–3 segments depending on distance:

| Distance | Segments |
|---|---|
| < 3 km | 1 |
| 3–6 km | 2 |
| > 6 km | 3 |

Each segment rolls `1d20 + stat_modifier` against DC. The DC scales with distance
and time of day:

```
DC = base_dc + floor(segment_km × distance_modifier) + time_modifier
```

Example with defaults (`base_dc=16`, `distance_modifier=2`):
- 2 km journey, single segment, daytime: `DC = 16 + floor(2 × 2) + 0 = 20`
- Same journey at night: `DC = 16 + 4 + 4 = 24`
- Roll of 14 + stealth modifier 3 = 17 → avoided at DC 20, triggered at DC 24

The stat used for the check is configurable (`stealth`, `dex`, `custom:awareness`,
`skill:perception`, etc.).

**Encounter nature** (1d20 after trigger):

| Roll | Category | Resolution |
|---|---|---|
| 1–5 | Dangerous | DM describes; waypoint created |
| 6–10 | Neutral | DM describes; waypoint created |
| 11–15 | Beneficial | DM describes; waypoint created |
| 16–20 | Special | DM describes; waypoint created |

Internally, the module categorizes encounters as Combat, Social, or Hazard (waypoint
created, party stops mid-journey) versus Loot or Flavor (auto-resolved, party
continues). The DM's rules file maps encounter categories to specific types.

**Waypoints** are temporary `locations.json` entries placed at the segment midpoint
between origin and destination. They have two connections: forward (continue) and
back (return to origin). Once the party leaves, the waypoint is cleaned up.

Manual check (bypasses automatic trigger):

```bash
bash tools/dm-encounter.sh check "Village" "Ruins" 2000 forest
```

---

### Encounter system configuration

```bash
bash tools/dm-encounter.sh toggle            # enable / disable
bash tools/dm-encounter.sh set-base-dc 18   # harder to avoid
bash tools/dm-encounter.sh set-distance-mod 3
bash tools/dm-encounter.sh set-stat custom:awareness
bash tools/dm-encounter.sh set-time-mod Night 6
bash tools/dm-encounter.sh status
```

---

### Map rendering

ASCII map scaled to location coordinates, printed to terminal:

```bash
bash tools/dm-map.sh                # default 80×40 ASCII
bash tools/dm-map.sh --color        # ANSI colors
bash tools/dm-map.sh --minimap      # compact view around current location
bash tools/dm-map.sh --width 120 --height 60
bash tools/dm-map.sh --no-labels    # coordinates only, no names
```

Interactive GUI (requires `pygame`):

```bash
bash tools/dm-map.sh --gui
# Pan with mouse drag, zoom with scroll wheel
```

---

## Configuration reference

All encounter settings live in `campaign-overview.json` under
`campaign_rules.encounter_system`:

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
  },
  "path_preferences": {}
}
```

`min_distance_meters` — journeys shorter than this skip encounter checks entirely.

`stat_to_use` accepts:
- standard D&D ability: `stealth`, `dex`, `con`
- skill: `skill:perception`
- custom stat: `custom:awareness` (value range 0–100, mapped to modifier via `(value - 50) // 10`)

`path_preferences` is populated automatically by `decide` — do not edit manually.

Location data shape:

```json
{
  "Village": {
    "coordinates": { "x": 0, "y": 0 },
    "connections": [
      {
        "to": "Old Mill",
        "distance_meters": 800,
        "bearing": 90,
        "terrain": "forest"
      }
    ],
    "blocked_ranges": [
      {
        "from": 160,
        "to": 200,
        "reason": "sheer drop into ravine"
      }
    ]
  }
}
```

---

## Middleware interception points

This module intercepts two CORE tools via `.claude/modules/world-travel/middleware/`:

- **`dm-session.sh move`** — replaces the bare location write with distance/time
  calculation + automatic encounter check after the move completes
- **`dm-location.sh add`** — when `--from` and `--bearing` and `--distance` flags are
  present, delegates to `dm-navigation.sh add` for coordinate computation; plain `add`
  without those flags falls through to CORE unchanged

If the module is disabled, both tools behave as vanilla CORE.

---

## Use cases

- **Open-world survival** (STALKER, Fallout, Metro): coordinate map, radiation zones
  blocked by `blocked_ranges`, encounter frequency tuned by terrain and time
- **Wilderness hex crawl**: each hex is a location, distances reflect hex size,
  encounter DC set to taste
- **Realistic travel simulation**: `speed_kmh` from character sheet, time advances
  proportionally, encounters scale with distance traveled
- **Visual DM aid**: ASCII map in terminal or Pygame window on secondary monitor

---

## Running tests

```bash
uv run pytest .claude/modules/world-travel/tests/
```

Tests cover pathfinding edge cases (disconnected graph, loops, blocked arcs) and
encounter engine (DC calculation, segment count, waypoint coordinates).
