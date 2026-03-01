# World Travel — DM Rules

## Navigation

```bash
bash tools/dm-session.sh move "Temple"
bash tools/dm-session.sh move "Temple" --speed-multiplier 1.5
```

Move = distance/time calc + clock advance + auto encounter check.

Route decisions (no direct connection):
```bash
bash .claude/modules/world-travel/tools/dm-navigation.sh decide "Village" "Temple"
```

Direction blocking:
```bash
bash .claude/modules/world-travel/tools/dm-navigation.sh block "Cliff Edge" 160 200 "Steep cliff drop"
bash .claude/modules/world-travel/tools/dm-navigation.sh unblock "Cliff Edge" 160 200
```

Map:
```bash
bash .claude/modules/world-travel/tools/dm-map.sh             # ASCII
bash .claude/modules/world-travel/tools/dm-map.sh --minimap   # nearby
bash .claude/modules/world-travel/tools/dm-map.sh --gui       # Pygame GUI
```

---

## Random Encounters

Auto-fires after every `move`. Manual:
```bash
bash .claude/modules/world-travel/tools/dm-encounter.sh check "Village" "Ruins" 2000 open
```

| Type | Waypoint? | Action |
|------|-----------|--------|
| Combat | Yes | Enemies, initiate combat |
| Social | Yes | NPC encounter, dialogue |
| Hazard | Yes | Obstacle (anomaly, trap) |
| Loot | No | Items found |
| Flavor | No | Atmosphere, continue |

Waypoint = temp location mid-journey. Player: **Forward** or **Back**. Removed after leaving.

DC: `base_dc + (segment_km × distance_modifier) + time_modifier`. Max 30.

Skip encounters when: system disabled, distance < 300m, teleportation, movement inside building, middleware already ran it.

---

## Hierarchical Locations

One flat `locations.json`, tree via `parent`/`children` fields.

| Type | Coordinates | Children | Examples |
|------|------------|----------|----------|
| `world` | Yes | No | Map point |
| `compound` | Yes (top-level) | Yes | City, ship, castle |
| `interior` | No | No | Room, hall |

### Create

```bash
# Compound
bash .claude/modules/world-travel/tools/dm-hierarchy.sh create-compound "Город" --entry-points "Ворота"

# Rooms
bash .claude/modules/world-travel/tools/dm-hierarchy.sh add-room "Ворота" --parent "Город" --entry-point
bash .claude/modules/world-travel/tools/dm-hierarchy.sh add-room "Площадь" --parent "Город" --connections '[{"to": "Ворота"}]'

# Nested compound
bash .claude/modules/world-travel/tools/dm-hierarchy.sh create-compound "Замок" --parent "Город" --entry-points "Ворота замка"
```

### Entry Points

Interior with `is_entry_point: true` + `entry_config`:
- `on_enter`/`on_exit` — DM hint (NOT automated)
- `locked` — blocked until key/solution
- `hidden` — DM knows, player doesn't yet

### Navigate

```bash
bash .claude/modules/world-travel/tools/dm-hierarchy.sh enter "Город" --via "Ворота"
bash .claude/modules/world-travel/tools/dm-hierarchy.sh move "Площадь"
bash .claude/modules/world-travel/tools/dm-hierarchy.sh exit
```

### View

```bash
bash .claude/modules/world-travel/tools/dm-hierarchy.sh tree
bash .claude/modules/world-travel/tools/dm-hierarchy.sh tree "Город"
bash .claude/modules/world-travel/tools/dm-hierarchy.sh validate
```

### Player Position

Player MUST always be on `interior`, never on `compound` directly. Auto-resolves to first entry point on `dm-session.sh start`/`context`.

`location_stack` tracks full path: `["Город", "Замок", "Тронный зал"]`.

NPCs use `tags.locations[]` — association tags, not positional tracking. DM decides sublocation by narrative.

### Interior Rules

- No `coordinates` — GUI uses force-directed layout
- Connections are canonical (stored once, read bidirectionally)
- `diameter_meters` on compounds = visual size on global map

### GUI

- **Global**: top-level locations only. Compounds = squares.
- **Interior**: click compound → select. Click again / Enter button → drill down. Radial tree layout.
- **Breadcrumb**: `World > City > Castle > Room`. Click = navigate.
- **Player location**: highlighted on both global (parent compound) and interior views.
- **ESC**: go up. **R**: refresh.

---

## Vehicles

Vehicles = compounds with `mobile: true`.

### Create

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh create kestrel spacecraft "Станция Кестрел"
bash .claude/modules/world-travel/tools/dm-vehicle.sh add-room kestrel "Мостик" --from "Станция Кестрел" --bearing 90 --distance 10
```

`add-room` creates bidirectional connections automatically.

### Board / Exit

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh board kestrel
bash .claude/modules/world-travel/tools/dm-vehicle.sh board kestrel --room "Мостик"
bash .claude/modules/world-travel/tools/dm-vehicle.sh exit
```

Inside vehicle: `dm-session.sh move "Room"` is intercepted — no encounters, no time tick.

### Move Vehicle

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh move kestrel "Космостанция Зета-9"
bash .claude/modules/world-travel/tools/dm-vehicle.sh move kestrel --x 5000 --y 3200
```

**To named location**: stops at `stopping_distance` (sum of radii) — never overlaps target.
**To coordinates**: places exactly.

On move: ALL external connections are wiped and rebuilt by proximity (`proximity_radius_meters`). New connections inherit terrain from nearby location. Player inside = travels with vehicle.

### Status

```bash
bash .claude/modules/world-travel/tools/dm-vehicle.sh status
bash .claude/modules/world-travel/tools/dm-vehicle.sh map kestrel
```

---

## Terrain

Campaign-defined in `campaign-overview.json`:

```json
{
  "terrain_colors": {
    "space": [40, 40, 80],
    "nebula": [100, 50, 150],
    "forest": [50, 150, 50]
  }
}
```

No defaults. DM creates types per campaign. Unknown types use `default` fallback color.

---

## Arrival Awareness

On arrival at dangerous/unfamiliar locations, check passive Perception.

**Passive Perception** = 10 + Wisdom mod (+ proficiency if trained)

| Hidden Element | Typical DC |
|----------------|------------|
| Someone watching openly | 10 |
| Hidden watcher | 15 |
| Well-concealed trap | 15-18 |
| Secret door | 20+ |

- If passive beats DC → mention in description
- If passive fails → element remains hidden (note for later)
- If player actively searches → roll Perception vs DC

## Arrival Narration

Use [Narration](#narration) workflow for the new scene.
