# /gm - Your AI Game Master

One command. Instant immersion.

---

## SUBCOMMAND ROUTING

When user invokes `/gm <subcommand>`, route to the appropriate section:

| Subcommand | Action |
|------------|--------|
| (none) | Continue to STEP 0: CAMPAIGN SELECTION below |
| save | Jump to SAVE SESSION section |
| character | Jump to CHARACTER DISPLAY section |
| overview | Jump to CAMPAIGN OVERVIEW section |
| status | Run `bash tools/gm-overview.sh` and display results |
| end | Jump to ENDING SESSION section |
| choices [on\|off\|toggle] | Run `bash tools/gm-session.sh choices <arg>`, confirm the new play style, and continue the current scene in it |

---

## ACTION MENU (PLAY STYLE)

The GM can end each beat with a few numbered action options, or with an open
prompt and no menu. This is a per-campaign, player-togglable preference
(`preferences.action_menu`, default ON) surfaced in `gm-session.sh context`.
Beat shape and pacing live in CLAUDE.md and the session brief — do not duplicate
them here.

- Toggle explicitly: `bash tools/gm-session.sh choices on|off|toggle` (no arg shows state).
- Toggle by asking mid-play ("stop giving me choices", "give me options again"):
  detect the intent, run the command to persist it, then continue the scene in
  the new style without re-narrating.

When OFF, still resolve actions and prompt the player — just close with an open
question instead of a numbered list.

---

## STEP 0: CAMPAIGN SELECTION

**ALWAYS display the campaign selection menu first.**

```bash
bash tools/gm-campaign.sh list
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

- **If user picks a campaign number** → `bash tools/gm-campaign.sh switch <name>` then go to CONTINUE CAMPAIGN
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
bash tools/gm-campaign.sh create "one-shot" --campaign-name "One-Shot Adventure"
bash tools/gm-campaign.sh switch "one-shot"
bash tools/gm-location.sh add "The Rusty Tankard" "A cozy tavern with worn wooden tables"
bash tools/gm-npc.sh create "Barkeep Tom" "grizzled innkeeper" "friendly"
```

### 4. Begin Adventure
Jump directly to scene setting:
- Skip extensive world-building
- Focus on immediate action
- 3-5 encounters maximum
- Option to convert to full campaign at end

---

## ENTERING A WORLD (identity-first — the default)

A player arrives with an "I love this book" spike. Spending it on ability scores wastes it,
so entry costs **one question**, not nine steps: *"Who are you in this world?"*

Ask it in your own voice, in the world's tone, and offer three doors — someone from the
book, someone of their own, or no one yet. Whatever they answer, persist it and start
playing; mechanics are inferred silently and can be filled in later during play.

```bash
bash tools/gm-player.sh onboard canon "<NPC name>"                 # a character from the source
bash tools/gm-player.sh onboard original "<name>" "<one-line concept>"
bash tools/gm-player.sh onboard nameless                           # a nameless traveler
```

- **canon** lifts that NPC's sheet and canonical voice from `npcs.json` — offer names that
  actually exist in this world (scene context and `gm-npc.sh` know who they are).
- **original** takes a name and a single line ("a thief with a debt"). Don't interrogate.
- **nameless** is a real answer, not a fallback — the world names them in play.

`onboard` refuses to overwrite a campaign that already has a PC (it names who is sitting
there). That refusal is a signal you asked the question at the wrong moment — check before
you offer. If the player really is handing the story to someone new, add `--replace`, which
archives the outgoing sheet to `fallen/` first.

The full builder is the **opt-in deep dive**: if the player wants to roll stats, pick a
class, and build a sheet properly, run `/create-character` instead. Offer it, never impose it.

---

## CONTINUE CAMPAIGN

### 🔒 MANDATORY STARTUP CHECKLIST

**Execute ALL steps before presenting the scene to the player. Do not skip any step.**

#### Step 1: Load Full Context (PRIMARY)
```bash
bash tools/gm-session.sh start
bash tools/gm-session.sh context
```
This single command gives you: character stats, party members (with recent events), pending consequences, campaign rules, location, and time. Read and internalize ALL of it.

**If there is no character yet** (no `character.json` / the context shows no active PC), don't
narrate a scene into a void and don't launch the 9-step builder — go to ENTERING A WORLD
below, ask the one question, then come back and finish the checklist.

**⚠️ Campaign Rules:** If the context output shows campaign-specific rules, enforce them throughout the session just like core rules. Each campaign is different.

#### Step 2: Verify Location (CRITICAL)
```bash
tail -30 world-state/campaigns/[campaign-name]/session-log.md
```
- [ ] Find the LAST session's ending location in the log
- [ ] Compare to location from Step 1
- [ ] **If mismatch**: Session log is truth. Run:
  ```bash
  bash tools/gm-session.sh move "[correct location]"
  ```

#### Step 3: Deep-Dive Party Context (IF NEEDED)

If the context summary isn't enough for a party member, get full details:
```bash
bash tools/gm-npc.sh status "[name]"
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

### Using Source Material (GM-Internal)

When `gm-session.sh start` or `move` runs, it queries source material for the current location. The context appears as `[GM Context: ...]` in the tool output - this is for **your eyes only**, not the player's.

**How to use GM Context:**
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
bash tools/gm-session.sh end "[brief summary of what happened]"
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
  /gm save · /gm character · /help
================================================================
```

---

## CHARACTER DEATH (mid-session hand-off)

PC death is **NOT** the end-session path above. Death does not close the game — it routes to the **Death Protocol** in CLAUDE.md and play continues with a new active PC.

When the PC dies (see Stakes & Death / 0-HP rules in CLAUDE.md):

1. **Persist first** — `bash tools/gm-player.sh kill "<name>" --cause "<how>"` (sets status dead, HP 0, stamps died_at), log it as a fact (`gm-note.sh`), record any triggered consequence (`gm-consequence.sh add`).
2. **Narrate the death** with weight. No menu yet.
3. **Offer the hand-off** (the show goes on — not GAME OVER). The three routes — take over a party member already in the scene, roll a new character, or step in as a canon figure from the source. Frame them however CLAUDE.md's Death Protocol calls for. (If solo with no party and no fitting canon figure, offer the last two only.)
4. **SWAP in the new PC:**
   - Party member → `bash tools/gm-player.sh become "<name>"` (copies their party sheet into character.json, archives the fallen PC to `fallen/`).
   - New character → spawn `create-character`, `gm-player.sh save-json '<json>'`, then `gm-player.sh set "<name>"`.
   - Canon figure → onboarding canon path → flesh out via `create-character` if thin → save to character.json → `gm-player.sh set "<name>"`.
5. **Bridge the fiction** (how/why control passes), update location/scene, then resume play. The dead hero stays in the world's memory — referenced, mourned, looted, avenged. Threads and clocks persist.

---

## SAVE SESSION

**Invoked via:** `/gm save`

Execute comprehensive save workflow:

### 1. End Session with Summary
```bash
bash tools/gm-session.sh end "[brief summary of key events]"
```

### 2. Verify State Updates
Ensure all changes from the session are persisted:
- HP changes → `gm-player.sh hp`
- Inventory changes → `gm-player.sh inventory`
- Gold changes → `gm-player.sh gold`
- NPC updates → `gm-npc.sh update`
- Location changes → `gm-session.sh move`
- Consequences → `gm-consequence.sh add`
- Facts → `gm-note.sh`

### 3. Run Verification
```bash
bash tools/gm-session.sh status
bash tools/gm-consequence.sh check
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

**Invoked via:** `/gm character`

### 1. Get Active Character
```bash
bash tools/gm-player.sh show
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

If no active character: don't print a sheet — ask the one question (see ENTERING A WORLD)
and route to `bash tools/gm-player.sh onboard canon|original|nameless ...`, mentioning
`/create-character` as the opt-in full builder for players who want the deep dive.

---

## CAMPAIGN OVERVIEW

**Invoked via:** `/gm overview`

### 1. Load Campaign Info
```bash
bash tools/gm-campaign.sh info
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
bash tools/gm-consequence.sh check
```

---

That's it. One command. Infinite adventure.
