# /new-game - Create Your World

Create a complete D&D campaign world from scratch through a guided interview.

---

## PHASE 1: CAMPAIGN NAME

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CREATE YOUR WORLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Let's build a unique campaign world together.

QUESTION 1 of 4: What's your campaign called?

This will be the name of your save folder.
```

Wait for user response. Store as `CAMPAIGN_NAME`.

### Check if Campaign Already Exists
```bash
bash tools/dm-campaign.sh list
```

If a campaign with this name already exists, ask user:
- Switch to existing campaign?
- Choose a different name?
- Delete and recreate? (requires confirmation)

### Create New Campaign
```bash
bash tools/dm-campaign.sh create "<CAMPAIGN_NAME>"
bash tools/dm-campaign.sh switch "<CAMPAIGN_NAME>"
```

---

## PHASE 1.5: MODULE SELECTION

Run after campaign is created and switched (so modules persist to campaign-overview.json).

### 1. List available modules
```bash
bash tools/dm-module.sh list-verbose
```

### 2. Display module menu

```
================================================================
  ╔═══════════════════════════════════════════════════════════╗
  ║              CONFIGURE MODULES                            ║
  ╚═══════════════════════════════════════════════════════════╝
================================================================

  [1] ✅ <id>  — <description, 5 words max>  ← default
  [2] ❌ <id>  — <description, 5 words max>
  ...

  ────────────────────────────────────────────────────────────
  💡 RECOMMENDED FOR THIS CAMPAIGN:
  Based on campaign name and tone, suggest which modules make
  sense. E.g. for survival/STALKER → custom-stats + firearms.
  For classic D&D → inventory only. For open world → world-travel.
  Write 1-2 sentences why each suggested module fits the vibe.
  ────────────────────────────────────────────────────────────
  Type numbers to toggle (e.g. "1 2") or ENTER to keep current.

================================================================
```

### 3. Apply selection
```bash
bash tools/dm-module.sh activate <module-name>    # for each enabled
bash tools/dm-module.sh deactivate <module-name>  # for each disabled
```

### 4. Load module rules into context
```bash
bash tools/dm-active-modules-rules.sh
```

Rules are now in context — use them for all world-building that follows.

---

## PHASE 1.6: LOAD MODULE CREATION RULES

Load creation-specific instructions from active modules:

```bash
bash tools/dm-active-modules-creation-rules.sh
```

These rules tell you HOW to handle world-building for each active module:
- **custom-stats**: Which stats to propose, how to configure them
- **world-travel**: How to generate locations with coordinates and encounters
- **inventory-system**: Starting equipment philosophy and item initialization
- **firearms-combat**: Weapon presets and firearms system configuration

**The creation rules augment (not replace) the phases below.**
Follow module-specific instructions when they apply to that phase.

---

## PHASE 2: TONE

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CREATE YOUR WORLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION 2 of 4: What's the tone of your adventure?

  1) Heroic    - Classic fantasy, good vs evil, heroes rise
  2) Gritty    - Dark, morally gray, survival matters
  3) Whimsical - Lighthearted, humor, fairy-tale vibes
  4) Epic      - Grand scale, world-shaking consequences
```

Use AskUserQuestion with these options:
- **Heroic** - Classic good vs evil, brave heroes, epic quests
- **Gritty** - Moral ambiguity, harsh consequences, survival
- **Whimsical** - Humor, silly situations, fairy-tale atmosphere
- **Epic** - Grand scale, legendary deeds, world-changing events

Store the user's choice as `TONE`.

---

## PHASE 3: MAGIC LEVEL

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CREATE YOUR WORLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION 3 of 4: How common is magic?

  1) Rare      - Magic is mysterious, feared, or forgotten
  2) Uncommon  - Magic exists but practitioners are special
  3) Common    - Magic is part of everyday life
  4) Wild      - Magic is everywhere and unpredictable
```

Use AskUserQuestion with these options:
- **Rare** - Magic is feared and mysterious; mages are legends
- **Uncommon** - Magic exists but casters are special; items are valuable
- **Common** - Magic shops exist, many know cantrips
- **Wild** - Magic saturates everything; unpredictable effects

Store as `MAGIC_LEVEL`.

---

## PHASE 4: SETTING TYPE

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CREATE YOUR WORLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION 4 of 4: What kind of setting?

  1) Medieval Village  - Small town, local threats
  2) Frontier Outpost  - Edge of civilization, wilderness
  3) City Streets      - Urban intrigue, factions, crime
  4) Ancient Ruins     - Exploration, lost civilizations
  5) Coastal Port      - Trade, pirates, sea adventure
  6) Surprise me!      - Random based on your answers
```

Use AskUserQuestion with these options:
- **Medieval Village** - Classic small town with local threats and familiar faces
- **Frontier Outpost** - Edge of civilization, wilderness dangers, pioneer spirit
- **City Streets** - Urban intrigue, political factions, criminal underworld
- **Ancient Ruins** - Exploration focus, mysteries of lost civilizations
- **Coastal Port** - Trade hub, pirates, sea adventures, diverse travelers
- **Surprise me!** - Generate a setting based on tone and magic choices

Store as `SETTING_TYPE`.

---

## PHASE 5: WORLD GENERATION

Display progress:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GENERATING YOUR WORLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Campaign: "<CAMPAIGN_NAME>"
Tone: <TONE> | Magic: <MAGIC_LEVEL> | Setting: <SETTING_TYPE>

Building your world...

  ├─ Creating starting location.... [working]
  ├─ Populating with NPCs.......... [working]
  ├─ Weaving plot threads.......... [working]
  └─ Establishing connections...... [working]
```

### Generate Starting Location

Based on the setting type, create the starting location with full detail:
- 100+ word description with sensory details
- 3+ named NPCs with personalities
- Connections to adjacent areas
- Local secrets and current events

```bash
bash tools/dm-location.sh add "[Starting Location Name]" "center of the settlement"
bash tools/dm-location.sh describe "[Starting Location Name]" "[detailed description]"
```

### Generate Supporting Locations

Create 3-4 connected locations with moderate detail (50-80 words each):
- A place for services/commerce
- A place for authority/knowledge
- A place representing danger or mystery

```bash
bash tools/dm-location.sh add "[Location Name]" "[position relative to start]"
bash tools/dm-location.sh connect "[Start]" "[Location]" "[path description]"
```

### Generate NPCs

Create 6 interconnected NPCs:
1. **Quest Giver A** - Has a problem to solve
2. **Quest Giver B** - Rival with conflicting goals
3. **Service Provider** - Merchant or craftsperson
4. **Information Source** - Knows local secrets
5. **Mysterious Figure** - Hints at larger plots
6. **Local Character** - Adds flavor and humor

```bash
bash tools/dm-npc.sh create "[Name]" "[description]" "[attitude]"
bash tools/dm-npc.sh tag-location "[Name]" "[location]"
```

### Generate Plot Hooks

Create three interconnected storylines:

**Local Conflict** (1-3 sessions)
- Affects starting location directly
- Can be partially resolved quickly

**Regional Mystery** (4-8 sessions)
- Spans multiple locations
- Requires investigation

**World Event** (campaign-long)
- Background threat building
- Only hints initially

```bash
bash tools/dm-note.sh "plot_local" "[local conflict description]"
bash tools/dm-note.sh "plot_regional" "[regional mystery description]"
bash tools/dm-note.sh "plot_world" "[world event hints]"
```

### Schedule Consequences

Plant future events:

```bash
bash tools/dm-consequence.sh add "[Hook to draw players in]" "next session"
bash tools/dm-consequence.sh add "[Strange event occurs]" "2 days"
bash tools/dm-consequence.sh add "[Rumor arrives from afar]" "1 week"
```

### Update Status

As each element completes:
```
  ├─ Creating starting location.... done
  ├─ Populating with NPCs.......... done (6 characters)
  ├─ Weaving plot threads.......... done (3 storylines)
  └─ Establishing connections...... done
```

---

## PHASE 6: UPDATE CAMPAIGN OVERVIEW

```bash
CAMPAIGN_DIR=$(bash tools/dm-campaign.sh path)

uv run python -c "
import json
from datetime import datetime

# Load existing campaign overview
with open('$CAMPAIGN_DIR/campaign-overview.json', 'r') as f:
    data = json.load(f)

# Update with world-building details
data.update({
    'current_date': '1st day of Springrise, Year 1000',
    'time_of_day': 'Morning',
    'player_position': {
        'current_location': '[Starting location name]',
        'previous_location': None
    },
    'current_character': None,
    'session_count': 0
})

with open('$CAMPAIGN_DIR/campaign-overview.json', 'w') as f:
    json.dump(data, f, indent=2)
"
```

---

## PHASE 7: INITIALIZE SESSION LOG

```bash
CAMPAIGN_DIR=$(bash tools/dm-campaign.sh path)
cat > "$CAMPAIGN_DIR/session-log.md" << EOF
# Session Log - [CAMPAIGN_NAME]

**Tone**: [TONE]
**Magic Level**: [MAGIC_LEVEL]
**Setting**: [SETTING_TYPE]
**Started**: $(date -u +"%Y-%m-%d")

---

## Session 0: World Creation
**Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

### World Summary
- **Starting Location**: [Location name]
- **Initial NPCs**: [List the 6 NPC names]
- **Plot Hooks**: Local conflict, regional mystery, world event

Ready for character creation.

---
EOF
```

---

## PHASE 8: DISPLAY SUMMARY

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YOUR WORLD IS READY!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Campaign: "[CAMPAIGN_NAME]"
Tone: [TONE] | Magic: [MAGIC_LEVEL] | Setting: [SETTING_TYPE]

Starting Location: [Location Name]
   [First sentence of description]

Key NPCs:
   • [NPC 1] - [role]
   • [NPC 2] - [role]
   • [NPC 3] - [role]
   • [NPC 4] - [role]
   • [NPC 5] - [role]
   • [NPC 6] - [role]

Active Plot Hooks:
   • LOCAL: [One line summary]
   • REGIONAL: [One line summary]
   • WORLD: [One line summary]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PHASE 9: TRANSITION TO CHARACTER CREATION

Display:

```
Your world awaits its hero!

Now let's create your character...
```

Then automatically run `/create-character` to guide the user through character creation.

---

## ERROR RECOVERY

**Campaign already exists**: Offer to switch, rename, or recreate

**NPC/location creation fails**: Retry with different name

**JSON file corruption**: Reinitialize empty file structure

---

## COMPLETION CHECKLIST

Before transitioning to character creation, verify:

- [ ] Campaign folder exists with all JSON files
- [ ] Starting location + 3-4 connected locations
- [ ] All locations connected via paths
- [ ] 6 NPCs with descriptions and locations
- [ ] 3-tier plot structure in facts.json
- [ ] 3+ consequences scheduled
- [ ] Session log initialized
- [ ] Campaign overview updated with settings
- [ ] Module-specific creation steps completed (custom-stats configured, firearms weapons set, etc.)

---

## AFTER /new-game: RECOMMENDED NEXT STEP

Once world creation and character creation are complete, display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WORLD READY — START PLAYING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your campaign is set up. To start playing:

  1. Clear this context window  (/clear or Ctrl+C / new chat)
  2. Run /dm

Why clear context?
  /new-game loaded creation rules and build instructions.
  /dm loads only the game rules your campaign needs.
  Smaller context = faster, more focused sessions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
