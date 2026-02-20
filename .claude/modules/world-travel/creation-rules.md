# World Travel — Creation Rules

> Instructions for DM (Claude) when building a new campaign with this module active.
> Run DURING Phase 3–4 of /new-game (location generation), replacing the default location creation.

---

## Step 1: Determine World Scale

Ask the user before generating locations:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WORLD SCALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How big is your world?

  [1] LOCAL — village + 3-5 nearby points (< 5 km)
      One day's walk covers everything.

  [2] REGIONAL — town + surrounding area (5–50 km)
      Multiple days of travel, varied terrain.

  [3] CONTINENTAL — cities, wilderness, distant lands (50–500 km)
      Weeks of travel, major geographical features.

  [4] ABSTRACT — locations exist but distances don't matter
      Use named connections only, no coordinate map.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Scale [4] → skip coordinate assignment, use vanilla location creation.
Scales [1–3] → use `--from/--bearing/--distance` for ALL locations.

---

## Step 2: Set Travel Speed

Based on genre, suggest character speed:

| Genre | Default Speed |
|-------|--------------|
| Medieval fantasy | 4 km/h (walking) |
| Modern / STALKER | 5 km/h (walking), 60+ km/h (vehicle) |
| Sci-fi starship | Set per-vehicle, not per-character |
| Mounted | 12–16 km/h |

Write to character.json after character is created:
```bash
# speed_kmh is read by dm-navigation.sh move
# Set via dm-player.sh or direct JSON edit
```

---

## Step 3: Create Starting Location (Origin)

The FIRST location is the coordinate origin `(0, 0)`. Set manually:

```bash
bash tools/dm-location.sh add "[Starting Location]" "[description]"
```

Then set coordinates directly:
```python
uv run python -c "
import json
CAMPAIGN_DIR = '$(bash tools/dm-campaign.sh path)'
with open(f'{CAMPAIGN_DIR}/locations.json') as f:
    locs = json.load(f)
locs['[Starting Location]']['coordinates'] = {'x': 0, 'y': 0}
with open(f'{CAMPAIGN_DIR}/locations.json', 'w') as f:
    json.dump(locs, f, indent=2, ensure_ascii=False)
"
```

---

## Step 4: Generate Connected Locations

For each additional location, ALWAYS use `--from/--bearing/--distance`:

```bash
bash tools/dm-location.sh add "[Location Name]" "[description]" \
  --from "[Reference Location]" \
  --bearing <0-359> \
  --distance <meters> \
  --terrain <road|forest|mountain|urban|wasteland|space|internal>
```

### How Many Locations to Generate

| Scale | Starting Locations |
|-------|--------------------|
| LOCAL | 4–6 (hub + 3–5 surrounding) |
| REGIONAL | 6–10 (town + villages + 2–3 wilderness) |
| CONTINENTAL | 8–12 (cities + roads + wilderness) |

### Terrain Types & Distance Guidelines

| Terrain | Typical Distance | Travel Speed Multiplier |
|---------|-----------------|------------------------|
| road | 500–5000m | 1.0× |
| forest | 1000–3000m | 0.7× |
| mountain | 2000–8000m | 0.5× |
| urban | 100–1000m | 1.0× |
| wasteland | 1000–10000m | 0.8× |
| space | 1000–50000m | depends on ship |
| internal | 10–200m | 1.0× (inside buildings/ships) |

### Bearing Guidelines

Place locations narratively:
- Village to the north? → bearing 0°
- Forest to the east? → bearing 90°
- Ruins southwest? → bearing 225°

---

## Step 5: Configure Encounter System

Ask the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RANDOM ENCOUNTERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enable random encounters during travel?

  [1] YES — encounters trigger automatically on every move
  [2] NO  — pure exploration, no random interruptions

If YES:
  Difficulty: [EASY / MEDIUM / HARD]
  (Easy = base DC 12, Medium = 16, Hard = 20)

  Stat for avoiding: [stealth / perception / dex / custom:awareness]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Write to campaign-overview.json:
```json
{
  "campaign_rules": {
    "encounter_system": {
      "enabled": true,
      "base_dc": 16,
      "distance_modifier": 2,
      "stat_to_use": "stealth",
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

---

## Step 6: Show Map After Creation

After all locations are added:

```bash
bash .claude/modules/world-travel/tools/dm-map.sh
```

Display the ASCII map in the session summary so the user sees the world layout.

---

## Step 7: Vehicles (Optional)

If the campaign involves ships, dungeons, or cities with interiors, ask:

```
Does your world have any locations with interior maps?
(ships, space stations, large dungeons, city districts)

[Y] Set up vehicle/interior system
[N] Skip
```

If YES — guide through `dm-vehicle.sh create` for each interior location.

---

## Notes

- NEVER use `dm-location.sh add` without `--from/--bearing/--distance` except for the origin
- If scale is ABSTRACT → skip this entire module's creation flow, fall back to default new-game location creation
- The starting location coordinates must be set BEFORE adding dependent locations
- Always show the map at the end — it's the payoff for all the bearing/distance work
