# /dm-continue - Play the Game

---

## SUBCOMMAND ROUTING

| Subcommand | Action |
|------------|--------|
| (none) | Continue to MANDATORY STARTUP CHECKLIST |
| save | Jump to SAVE SESSION |
| character | Jump to CHARACTER DISPLAY |
| overview | Jump to CAMPAIGN OVERVIEW |
| status | Run `bash tools/dm-overview.sh` and display |
| end | Jump to ENDING SESSION |

---

## 🔒 MANDATORY STARTUP CHECKLIST

**Execute ALL steps before presenting the scene. Do not skip.**

### Step 1: Load Full Context
```bash
bash tools/dm-active-modules-rules.sh 2>/dev/null > /tmp/dm-rules.md
bash tools/dm-campaign-rules.sh 2>/dev/null >> /tmp/dm-rules.md
bash tools/dm-session.sh start
bash tools/dm-session.sh context
```
Then use the **Read tool** to read `/tmp/dm-rules.md` — this ensures the FULL rules are loaded (Bash output gets truncated, Read does not).

Read and internalize ALL of it: DM rules, character stats, party, pending consequences, campaign rules, location, time.

**⚠️ Campaign Rules:** The `campaign-rules.md` is appended above — enforce ALL campaign-specific rules (stat formulas, tech bonuses, population structure, era mechanics) throughout the session.

### Step 2: Verify Location
```bash
tail -30 world-state/campaigns/[campaign-name]/session-log.md
```
- Find LAST session's ending location
- Compare to Step 1 location
- **If mismatch**: session log is truth → `bash tools/dm-session.sh move "[correct location]"`

### Step 3: Party Context (if needed)
```bash
bash tools/dm-npc.sh status "[name]"
```

### Step 4: Mental Model
- [ ] WHERE is the party?
- [ ] WHEN is it?
- [ ] WHO is present?
- [ ] WHAT consequences are pending?
- [ ] WHY are they here?

**Only after ALL steps → present the scene.**

---

### Using Source Material (DM-Internal)

`[DM Context: ...]` in tool output = for your eyes only. Synthesize into narrative, never paste raw.

---

## GAMEPLAY LOOP

For every player action:

1. **Understand Intent** — what workflow applies?
2. **Execute** — use tools invisibly
3. **Persist** — save ALL state changes BEFORE narrating
4. **Narrate Result**
5. **Enforce Campaign Rules**
6. **Check XP** — after significant scenes
7. **Ask** — "What do you do?"

Repeat.

---

## ENDING SESSION

```bash
bash tools/dm-session.sh end "[brief summary]"
```

```
================================================================
  SESSION COMPLETE
  [Character] rests at [location]. Progress saved.
  Until next time, adventurer.
  /dm save · /dm-continue character · /help
================================================================
```

---

## SAVE SESSION

### 1. End with summary
```bash
bash tools/dm-session.sh end "[summary]"
```

### 2. Verify persisted
- HP → `dm-player.sh hp`
- Inventory → `dm-player.sh inventory`
- Gold → `dm-player.sh gold`
- NPCs → `dm-npc.sh update`
- Location → `dm-session.sh move`
- Consequences → `dm-consequence.sh add`
- Facts → `dm-note.sh`

### 3. Verify
```bash
bash tools/dm-session.sh status
bash tools/dm-consequence.sh check
```

---

## CHARACTER DISPLAY

```bash
bash tools/dm-player.sh show
```

Display full character sheet: stats, HP, AC, saves, skills, features, inventory.

---

## CAMPAIGN OVERVIEW

```bash
bash tools/dm-campaign.sh info
bash tools/dm-consequence.sh check
```

Display: location, time, character, sessions, NPC/location/fact counts, active consequences.
