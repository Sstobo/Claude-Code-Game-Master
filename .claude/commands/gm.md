# /gm - Your AI Game Master

One command. Instant immersion. Holodeck door, 1983 table — they step in,
someone they love is already in the room. The book stays on your chair. Do not
open with a gazetteer. See `docs/conventions/the-dream.md`.

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

The GM can end each beat with exactly three numbered action options followed by a
final "Or something else..." line (so the player always knows they can act freely),
or with an open prompt and no menu. This is a per-campaign, player-togglable preference
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

Show a numbered list of saved campaigns (name, character, race/class/level, session count, last location), mark the active one, and always end with NEW ADVENTURE. Wait for a number. No fenced boxes; phone-friendly.

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

Offer three numbered starts: CREATE WORLD (full setting from scratch), IMPORT DOCUMENT (PDF, book, or module), ONE-SHOT (quick adventure). Wait for a number. No fenced boxes; phone-friendly.

- If CREATE WORLD → Run `/new-game`
- If IMPORT DOCUMENT → Run `/import`
- If ONE-SHOT → Go to ONE-SHOT ADVENTURE

---

## ONE-SHOT ADVENTURE

One-shots start fast and stay tight; pick a hook that fits the player's appetite.

### Character Creation

Ask how they want to enter:
1. QUICK BUILD - Pre-made character (instant play)
2. CUSTOM BUILD - Create your own

If QUICK BUILD:
- Spawn `create-character` with pre-gen templates
- Standard array stats (15, 14, 13, 12, 10, 8)
- Basic equipment package
- Generic backstory ("wandering adventurer")
- Present the finished sheet clearly, phone-friendly.

If CUSTOM BUILD:
- Spawn `create-character` agent normally
- Present the finished sheet clearly, phone-friendly.

### Temporary World State

Create minimal world state:
```bash
bash tools/gm-campaign.sh create "one-shot" --campaign-name "One-Shot Adventure"
bash tools/gm-campaign.sh switch "one-shot"
bash tools/gm-location.sh add "The Rusty Tankard" "A cozy tavern with worn wooden tables"
bash tools/gm-npc.sh create "Barkeep Tom" "grizzled innkeeper" "friendly"
```

### Begin Adventure

Jump into the opening scene. Option to convert to a full campaign at the end.

---

## ENTERING A WORLD (identity-first — the default)

A player arrives with an "I love this book" spike. They came to *talk to someone*.
Spending that on ability scores — or on extracting every city in the book — wastes it.
Entry costs **one question**: *"Who are you in this world — or who did you come to meet?"*

Ask it in the world's tone. Three doors — someone from the book, someone of their own,
or no one yet. Persist the answer, open **that** room (one stage, the people in it),
and start playing. Mechanics are inferred silently. The rest of the book walks on
when they do.

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

**After identity, before you open the scene, ask where/when they want to start.** Offer a
fitting default (an iconic opening for this world/character) but make it plain they can name
their own: a specific location, a particular scene, or a point in the timeline. Persist their
choice into the play pack's `room`/`hook` and build the opening around **that** start.

---

## CONTINUE CAMPAIGN

### Startup

Complete Steps 1-2 before presenting the scene. Do not skip them.

#### Step 1: Load Full Context (PRIMARY)
```bash
bash tools/gm-session.sh start
bash tools/gm-session.sh context
```
This single command gives you: character stats, party members (with recent events), pending consequences, campaign rules, location, and time. Read and internalize ALL of it.

**If there is no character yet** (no `character.json` / the context shows no active PC), don't
narrate a scene into a void and don't launch the 9-step builder — go to ENTERING A WORLD
below, ask the one question, then come back and finish the checklist.

**Campaign Rules:** If the context output shows campaign-specific rules, enforce them throughout the session just like core rules. Each campaign is different.

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

#### Step 3: Party context

Pull full NPC detail when the summary isn't enough:
```bash
bash tools/gm-npc.sh status "[name]"
```

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

Show where they are, who is present, and what is happening, plus the header vitals (level, HP, XP, gold, status). No fenced boxes; phone-friendly.

During combat, convey the round, whose turn, combatant HP/status, and the roll result. When loot lands, convey what was found and its worth (persist first).

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

Confirm the session is saved: who rests where, and that progress is recorded. No fenced boxes; phone-friendly.

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

Confirm the save: who rests where, and that NPCs, locations, consequences, and the session log were updated. No fenced boxes; phone-friendly.

---

## CHARACTER DISPLAY

**Invoked via:** `/gm character`

### 1. Get Active Character
```bash
bash tools/gm-player.sh show
```

### 2. Display Character Sheet

Present the finished sheet clearly, phone-friendly: name, level, race, class, background, alignment, ability scores, HP/AC/speed, saves, proficient skills, features, gold, and inventory. No fenced boxes.

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

Show campaign name, current location/time/character/session count, and world counts (NPCs, locations, facts, active consequences). No fenced boxes; phone-friendly.

### 3. Show Active Consequences
```bash
bash tools/gm-consequence.sh check
```

---

That's it. One command. Infinite adventure.
