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

### Terrain & Colors [MANDATORY]

Set terrain types and RGB colors for the GUI map. Store in `campaign_rules.terrain_colors`.
Name the keys in the campaign's language (e.g. Russian campaign → Russian keys).

**Palette by genre:**
| Genre | Typical terrains + base colors |
|-------|-------------------------------|
| Fantasy/Medieval | forest [50,150,50], mountain [120,100,80], road [180,180,140], swamp [80,120,60], urban [160,160,160], river [60,120,200], plains [160,200,100] |
| Sci-fi/Space | space [10,10,40], nebula [100,50,150], station [80,80,100], asteroid [100,90,70], void [5,5,20] |
| Post-apo/STALKER | wasteland [140,120,80], radiation [100,160,60], ruins [100,90,80], anomaly [180,60,180], road [160,150,110] |
| Horror | forest [30,60,30], swamp [50,70,40], road [100,90,80], ruins [80,70,60], mist [150,150,170] |
| Stone Age | cave [80,70,60], river [60,120,200], forest [50,150,50], plains [160,200,100], mountain [120,100,80], beach [220,200,140], tundra [200,210,220] |

Add only terrains that realistically appear on this map. Write into `campaign_rules.terrain_colors` in campaign-overview.json.

### Location Sizes [MANDATORY]

Every location must have `diameter_meters` — controls circle size on GUI map (normalized to 8–40px).

| Type | diameter_meters |
|------|----------------|
| Building / cave / room / ship interior | 50–200 |
| Village / outpost / dungeon | 300–800 |
| Town / fortress / large ruin | 1000–3000 |
| City / large forest / mountain range | 3000–8000 |
| Region / continent zone | 10000+ |

Set sizes relative to each other — the GUI auto-normalizes, so ratios matter more than absolute values.

```bash
uv run python -c "
import json
CAMPAIGN_DIR = '$(bash tools/dm-campaign.sh path)'
with open(f'{CAMPAIGN_DIR}/locations.json') as f:
    locs = json.load(f)
locs['Location Name']['diameter_meters'] = 500
with open(f'{CAMPAIGN_DIR}/locations.json', 'w') as f:
    json.dump(locs, f, indent=2, ensure_ascii=False)
"
```

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
