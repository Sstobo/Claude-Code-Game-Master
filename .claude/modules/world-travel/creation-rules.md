# World Travel — Creation Rules

> For DM during /new-game Phase 3–4 (location generation).

## 1. World Scale

Ask the player:

| Scale | Size | Description |
|-------|------|-------------|
| LOCAL | < 5 km | Village + 3–5 points. One day covers everything. |
| REGIONAL | 5–50 km | Town + area. Multiple days, varied terrain. |
| CONTINENTAL | 50–500 km | Cities, wilderness. Weeks of travel. |
| ABSTRACT | — | Named connections only, no coordinate map. |

ABSTRACT → skip coordinates, use vanilla location creation.
LOCAL–CONTINENTAL → use `--from/--bearing/--distance` for ALL locations.

## 2. Travel Speed

| Genre | Speed |
|-------|-------|
| Medieval fantasy | 4 km/h walking |
| Modern | 5 km/h walking, 60+ km/h vehicle |
| Sci-fi starship | Per-vehicle |
| Mounted | 12–16 km/h |

Set `speed_kmh` in character.json.

## 3. Starting Location

First location = origin `(0, 0)`:

```bash
bash tools/dm-location.sh add "Starting Location" "description"
```

Then set coordinates:
```bash
uv run python -c "
import json
CAMPAIGN_DIR = '$(bash tools/dm-campaign.sh path)'
with open(f'{CAMPAIGN_DIR}/locations.json') as f:
    locs = json.load(f)
locs['Starting Location']['coordinates'] = {'x': 0, 'y': 0}
locs['Starting Location']['diameter_meters'] = 50
with open(f'{CAMPAIGN_DIR}/locations.json', 'w') as f:
    json.dump(locs, f, indent=2, ensure_ascii=False)
"
```

## 4. Add Locations

ALWAYS use `--from/--bearing/--distance` (except origin):

```bash
bash tools/dm-location.sh add "Forest" "Dark woods" \
  --from "Village" --bearing 90 --distance 2000 --terrain forest
```

| Scale | Starting count |
|-------|---------------|
| LOCAL | 4–6 |
| REGIONAL | 6–10 |
| CONTINENTAL | 8–12 |

### Terrain

No defaults. Define per campaign in `campaign-overview.json`:

```json
{ "terrain_colors": { "road": [180,180,140], "forest": [50,150,50] } }
```

| Genre | Typical terrains |
|-------|-----------------|
| Fantasy | road, forest, mountain, urban, swamp |
| Sci-fi | space, internal, nebula, asteroid, station |
| Modern | road, urban, wilderness, water |
| Post-apo | wasteland, ruins, road, radiation |

### Distances

| Terrain | Range | Speed mult |
|---------|-------|-----------|
| road/urban | 500–5000m | 1.0× |
| forest | 1000–3000m | 0.7× |
| mountain | 2000–8000m | 0.5× |
| space | 1000–50000m | ship-dependent |
| internal | 10–200m | 1.0× |

## 5. Encounters

Ask: enable random encounters? If yes:

```json
{
  "campaign_rules": {
    "encounter_system": {
      "enabled": true,
      "base_dc": 16,
      "distance_modifier": 2,
      "stat_to_use": "stealth",
      "time_dc_modifiers": { "Morning": 0, "Day": 0, "Evening": 2, "Night": 4 }
    }
  }
}
```

## 6. Compounds (optional)

If campaign has ships/cities/dungeons:

```bash
# Create compound
bash .claude/modules/world-travel/tools/dm-hierarchy.sh create-compound "Castle" --entry-points "Gate"

# Add rooms
bash .claude/modules/world-travel/tools/dm-hierarchy.sh add-room "Gate" --parent "Castle" --entry-point --connections '[{"to": "Hall"}]'
bash .claude/modules/world-travel/tools/dm-hierarchy.sh add-room "Hall" --parent "Castle"

# Mobile (ships)
bash .claude/modules/world-travel/tools/dm-hierarchy.sh create-compound "Ship" --mobile --entry-points "Airlock"

# Nested (castle inside city)
bash .claude/modules/world-travel/tools/dm-hierarchy.sh create-compound "Castle" --parent "City" --entry-points "Gate"

# Verify
bash .claude/modules/world-travel/tools/dm-hierarchy.sh tree
bash .claude/modules/world-travel/tools/dm-hierarchy.sh validate
```

Entry configs for guarded/hidden entrances:
```bash
bash .claude/modules/world-travel/tools/dm-hierarchy.sh add-room "Sewers" --parent "Castle" \
  --entry-point --entry-config '{"hidden": true, "on_enter": {"description": "Stealth DC 15"}}'
```

## 7. Show Map

```bash
bash .claude/modules/world-travel/tools/dm-map.sh
```

Always show ASCII map at the end.
