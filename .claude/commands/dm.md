# /dm - Your AI Dungeon Master

One command. Instant immersion.

---

## SUBCOMMAND ROUTING

When user invokes `/dm <subcommand>`, route to the appropriate section:

| Subcommand | Action |
|------------|--------|
| (none) | Continue to STEP 0: CAMPAIGN SELECTION below |
| save | Jump to SAVE SESSION section |
| character | Jump to CHARACTER DISPLAY section |
| overview | Jump to CAMPAIGN OVERVIEW section |
| status | Run `bash tools/dm-overview.sh` and display results |
| end | Jump to ENDING SESSION section |

---

## STEP 0: CAMPAIGN SELECTION

**ALWAYS display the campaign selection menu first.**

```bash
bash tools/dm-campaign.sh list
```

### Display Campaign Menu

```
================================================================
  ╔═══════════════════════════════════════════════════════════╗
  ║           SELECT YOUR ADVENTURE                           ║
  ╚═══════════════════════════════════════════════════════════╝
================================================================

  SAVED CAMPAIGNS
  ────────────────────────────────────────────────────────────
  [1] Campaign Name
      Character Name (Race Class L#) · X sessions
      Last: Location Name

  [2] Another Campaign
      Hero Name (Race Class L#) · X sessions
      Last: Some Location

  ────────────────────────────────────────────────────────────
  [N] ✨ NEW ADVENTURE - Start fresh

================================================================
  Enter number to continue:
================================================================
```

### Menu Logic

1. **List all campaigns** with number indices starting at 1
2. **Always include** `[N] NEW ADVENTURE` as the final option
3. **Show for each campaign:**
   - Campaign name
   - Character name, race, class, level
   - Session count
   - Last known location
4. **Mark active campaign** with `*` or `►` indicator
5. **Wait for user selection**

### After Selection

- **If user picks a campaign number** → `bash tools/dm-campaign.sh switch <name>` then go to CONTINUE CAMPAIGN
- **If user picks N (new)** → Go to NEW CAMPAIGN

---

## NEW CAMPAIGN

Display:
```
================================================================
  ╔═══════════════════════════════════════════════════════════╗
  ║              START A NEW ADVENTURE                        ║
  ╚═══════════════════════════════════════════════════════════╝
================================================================

  [1] 🌍 CREATE WORLD
      Build a full campaign setting from scratch

  [2] 📜 IMPORT DOCUMENT
      Import a PDF, book, or module

  [3] ⚔️  ONE-SHOT
      Quick adventure, play in minutes

================================================================
  Enter number:
================================================================
```

- If CREATE WORLD → Run `/new-game`
- If IMPORT DOCUMENT → Run `/import`
- If ONE-SHOT → Go to ONE-SHOT ADVENTURE

---

## ONE-SHOT ADVENTURE

### 1. Quick Scenario Generation
Generate a simple adventure hook:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ONE-SHOT ADVENTURE
  The Tavern's Call
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Roll for scenario type (internally):
- 1-2: Rescue mission (kidnapped merchant)
- 3-4: Monster hunt (creature terrorizing village)
- 5-6: Treasure hunt (map to ancient ruins)

### 2. Character Creation
Display:
```
Choose your hero:
1. QUICK BUILD - Pre-made character (instant play)
2. CUSTOM BUILD - Create your own

What's your choice?
```

If QUICK BUILD:
- Spawn `create-character` with pre-gen templates
- Standard array stats (15, 14, 13, 12, 10, 8)
- Basic equipment package
- Generic backstory ("wandering adventurer")

If CUSTOM BUILD:
- Spawn `create-character` agent normally
- Skip extensive backstory questions
- Focus on core mechanics only

### 3. Temporary World State
Create minimal world state:
```bash
bash tools/dm-campaign.sh create "one-shot" --campaign-name "One-Shot Adventure"
bash tools/dm-campaign.sh switch "one-shot"
bash tools/dm-location.sh add "The Rusty Tankard" "A cozy tavern with worn wooden tables"
bash tools/dm-npc.sh create "Barkeep Tom" "grizzled innkeeper" "friendly"
```

### 4. Begin Adventure
Jump directly to scene setting:
- Skip extensive world-building
- Focus on immediate action
- 3-5 encounters maximum
- Option to convert to full campaign at end

---

## CONTINUE CAMPAIGN

### Campaign Mode Check

Read `campaign-overview.json`:
```bash
bash tools/dm-campaign.sh info
```

If `"advanced_mode": true` → invoke `/dm-continue` instead (handles module rules, narrator styles, campaign rules templates).

Otherwise, continue below with the standard vanilla gameplay loop.

---

### 🔒 MANDATORY STARTUP CHECKLIST

**Execute ALL steps before presenting the scene to the player. Do not skip any step.**

#### Step 1: Load Full Context (PRIMARY)
```bash
bash .claude/modules/infrastructure/dm-active-modules-rules.sh 2>/dev/null > /tmp/dm-rules.md
bash tools/dm-session.sh start
bash tools/dm-session.sh context
```
Then use the **Read tool** to read `/tmp/dm-rules.md` — this ensures the FULL rules are loaded (Bash output gets truncated, Read does not).

Read and internalize ALL of it: DM rules, character stats, party members (with recent events), pending consequences, campaign rules, location, and time.

**⚠️ Campaign Rules:** If the context output shows campaign-specific rules, enforce them throughout the session just like core rules. Each campaign is different.

#### Step 2: Verify Location (CRITICAL)
```bash
tail -30 world-state/campaigns/[campaign-name]/session-log.md
```
- [ ] Find the LAST session's ending location in the log
- [ ] Compare to location from Step 1
- [ ] **If mismatch**: Session log is truth. Run:
  ```bash
  bash tools/dm-session.sh move "[correct location]"
  ```

#### Step 3: Deep-Dive Party Context (IF NEEDED)

If the context summary isn't enough for a party member, get full details:
```bash
bash tools/dm-npc.sh status "[name]"
```

For complex party members, also consider:
- [ ] **Equipment**: What weapons/items do they have?
- [ ] **Features/Abilities**: What can they do in combat/socially?
- [ ] **Relationships**: How do they relate to other party members?

**Why this matters:**
- Party members are not stat blocks - they are characters with voices
- Their recent events inform their current mood and behavior
- Source material context (from RAG) gives you their canonical voice

#### Step 4: Build Mental Model
Before narrating, confirm you know:
- [ ] WHERE is the party? (verified location)
- [ ] WHEN is it? (time of day)
- [ ] WHO is present? (personality, voice, recent events)
- [ ] WHAT consequences are pending?
- [ ] WHY are they here? (last session's ending context)

**⚠️ Only after completing ALL steps → Present the scene.**

---

### Using Source Material (DM-Internal)

When `dm-session.sh start` or `move` runs, it queries source material for the current location. The context appears as `[DM Context: ...]` in the tool output - this is for **your eyes only**, not the player's.

**How to use DM Context:**
- Read the context hints internally to understand the scene
- Ground descriptions in source material tone and details
- Reference specific sensory details from the original
- Match NPC dialogue to their canonical voice
- Capture the author's writing style and atmosphere

**CRITICAL: Do NOT paste raw passages into narrative.** Synthesize them into natural scene descriptions.

---

### Present Scene

Use the standard scene template from CLAUDE.md.

---

## GAMEPLAY LOOP

Now you're playing. For every player action, follow the workflows in CLAUDE.md:

1. **Understand Intent** - What workflow applies?
2. **Execute** - Use tools invisibly
3. **Persist** - Save all state changes
4. **Narrate Result** - Describe what happens
5. **Enforce Campaign Rules** - Apply any campaign-specific rules from campaign-overview.json's `campaign_rules` section
6. **Check for XP** - After significant scenes
7. **Ask** - "What do you do?"

Repeat.

---

## ENDING SESSION

When player says they're done:

```bash
bash tools/dm-session.sh end "[brief summary of what happened]"
```

Display:
```
================================================================
  SESSION COMPLETE
  --------------------------------------------------------
  [Character] rests at [location].
  Progress saved.
================================================================

  Until next time, adventurer.

================================================================
  /dm save · /dm character · /help
================================================================
```

---

## SAVE SESSION

**Invoked via:** `/dm save`

Execute comprehensive save workflow:

### 1. End Session with Summary
```bash
bash tools/dm-session.sh end "[brief summary of key events]"
```

### 2. Verify State Updates
Ensure all changes from the session are persisted:
- HP changes → `dm-player.sh hp`
- Inventory changes → `dm-player.sh inventory`
- Gold changes → `dm-player.sh gold`
- NPC updates → `dm-npc.sh update`
- Location changes → `dm-session.sh move`
- Consequences → `dm-consequence.sh add`
- Facts → `dm-note.sh`

### 3. Run Verification
```bash
bash tools/dm-session.sh status
bash tools/dm-consequence.sh check
```

### 4. Display Confirmation
```
================================================================
  SESSION SAVED
  --------------------------------------------------------
  [Character] rests at [location].
  All progress has been saved.

  [X] NPCs updated
  [X] Locations recorded
  [X] Consequences tracked
  [X] Session log updated
================================================================
```

---

## CHARACTER DISPLAY

**Invoked via:** `/dm character`

### 1. Get Active Character
```bash
bash tools/dm-player.sh show
```

### 2. Display Character Sheet

```
================================================================
  CHARACTER SHEET
================================================================

  [NAME]
  Level [#] [Race] [Class]
  Background: [Background]
  Alignment: [Alignment]

  --------------------------------------------------------
  STATS
  --------------------------------------------------------
  STR [##] (+#)  |  DEX [##] (+#)  |  CON [##] (+#)
  INT [##] (+#)  |  WIS [##] (+#)  |  CHA [##] (+#)

  --------------------------------------------------------
  COMBAT
  --------------------------------------------------------
  HP: [current]/[max]    AC: [##]    Speed: 30 ft

  --------------------------------------------------------
  SAVING THROWS
  --------------------------------------------------------
  STR +#  |  DEX +#  |  CON +#
  INT +#  |  WIS +#  |  CHA +#

  --------------------------------------------------------
  SKILLS (Proficient)
  --------------------------------------------------------
  [Skill Name] +#
  ...

  --------------------------------------------------------
  FEATURES & TRAITS
  --------------------------------------------------------
  * [Feature 1]
  * [Feature 2]
  ...

  --------------------------------------------------------
  EQUIPMENT & INVENTORY
  --------------------------------------------------------
  Gold: [##] gp

  Equipped:
  * [Armor]
  * [Weapon]

  Carried:
  * [Item 1]
  * [Item 2]
  ...

================================================================
```

If no active character: "No active character. Create one with /create-character"

---

## CAMPAIGN OVERVIEW

**Invoked via:** `/dm overview`

### 1. Load Campaign Info
```bash
bash tools/dm-campaign.sh info
```

### 2. Display Campaign State

```
================================================================
  [CAMPAIGN NAME]
================================================================

CURRENT STATE
  Location: [current_location]
  Time: [time_of_day] on [current_date]
  Character: [current_character]
  Sessions: [session_count]

WORLD STATISTICS
  NPCs: [count]
  Locations: [count]
  Facts: [count]
  Active Consequences: [count]
================================================================
```

### 3. Show Active Consequences
```bash
bash tools/dm-consequence.sh check
```

---

That's it. One command. Infinite adventure.
