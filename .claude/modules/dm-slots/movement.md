## Movement <!-- slot:movement -->

### Trigger Conditions
- "I go to [location]"
- "We travel to..."
- Any location change

### Phase 0: Check for Dungeon
Is current location a dungeon room (has `dungeon` field in locations.json)?
- **Yes** → Use [Dungeon Exploration](#dungeon-exploration)
- **No** → Continue with standard movement

### Phase 1: Validate Destination
```bash
bash tools/dm-search.sh "[destination_name]"
```
- Is destination reachable from current location?
- Any obstacles or requirements?

### Phase 2: Calculate Travel Time

| Distance | Time |
|----------|------|
| Adjacent room | 1 minute |
| Different floor | 2-5 minutes |
| Next building | 5-10 minutes |
| Across district | 15-30 minutes |
| Nearby (<5 miles) | 1-2 hours |
| Short journey (5-20 mi) | 2-8 hours |
| Day trip (20-30 mi) | 8-10 hours |

**Modifiers:** Stealth (×2), Running (÷2), Difficult terrain (×2), Mounted (×0.75)

### Movement Speed Defaults
| Mode | Speed |
|------|-------|
| Careful/Sneaking | 100 ft/minute |
| Normal Walk | 300 ft/minute |
| Hustle | 600 ft/minute |
| Running | 1200 ft/minute (Con check) |
| Overland Walk | 3 miles/hour, 24 miles/day |
| Overland Mounted | 4 miles/hour, 32 miles/day |

### Special Movement Types
- **Stealth**: Roll Stealth vs passive Perception; double travel time
- **Chase/Flee**: Opposed Athletics/Acrobatics; 3 successes wins
- **Teleportation**: Instant arrival, no time passes, still check consequences
- **Fast Travel**: Known safe routes skip to destination with appropriate time

### Phase 3: Update World State

**For overland/normal movement:**
```bash
bash tools/dm-session.sh move "[new_location]"
```
- Auto-creates destination if it doesn't exist
- Auto-creates bidirectional connections from previous location
- Auto-checks consequences

**For dungeons/buildings/special locations (basements, labs, etc.):**

If destination doesn't exist yet, create it manually FIRST:
```bash
# Create the location
bash tools/dm-location.sh add "[location_name]" "[description]"

# Create connection manually
bash tools/dm-location.sh connect "[from]" "[to]" --terrain [type] --distance [meters]

# Then move
bash tools/dm-session.sh move "[location_name]"
```

**Why manual for dungeons?**
- More control over terrain type (underground, cave, building_interior)
- Prevents accidental auto-connections to wrong places
- Allows setting specific distance (stairs = 10m, long corridor = 100m)

**Time advancement (if needed):**
```bash
# Option A: Advance by hours (clock auto-advances)
bash tools/dm-time.sh "Утро" "18 октября 2024" --elapsed 2

# Option B: Advance to exact time (auto-calculates elapsed)
bash tools/dm-time.sh "_" "18 октября 2024" --to 14:30

# Option C: Set exact clock without elapsed
bash tools/dm-time.sh "09:00" "18 октября 2024"
```
**NOTE:** See State Persistence for time/consequence tick rules.

### Phase 3.5: Arrival Awareness (Optional)
Use when arriving at dangerous/unfamiliar locations or where ambush is likely.

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

### Phase 4: Arrival Narration
Use [Narration](#narration) workflow for the new scene.

<!-- /slot:movement -->

---
