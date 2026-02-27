## Social (NPC Interaction)

### Trigger Conditions
- "I talk to [name]"
- "I ask [NPC] about..."
- Social encounter initiated

### Phase 1: Load NPC Context
```bash
bash tools/dm-search.sh "[npc_name]"
bash tools/dm-npc.sh status "[name]"
```
Check: Previous interactions, current attitude, active quests involving them.

### Phase 2: Attitude Check

Based on history and state:
- **Friendly**: Helpful, open, warm
- **Neutral**: Professional, cautious
- **Hostile**: Dismissive, aggressive, cold

### Phase 3: Social Mechanics

**When to Roll:**

| Skill | DC by Difficulty | When to Use |
|-------|------------------|-------------|
| Persuasion | Friendly 10, Neutral 15, Hostile 20 | Change mind |
| Deception | Plausible 10, Questionable 15, Outrageous 20 | Hide truth |
| Intimidation | Weak-willed 10, Average 15, Strong-willed 20 | Force compliance |
| Insight | Opposed by Deception, or DC 10-20 | Read person |

**Insight Details:**
- Detect lies: Opposed roll vs target's Deception
- Read emotions: DC 10-15
- Understand motives: DC 15-20

**Modifiers:** Unreasonable request +5 DC, Good rapport -2 DC

**No Roll Needed:**
- Asking for public information
- Normal commerce at listed prices
- Casual conversation
- Giving items/money freely

### Phase 4: Update NPC Memory
```bash
bash tools/dm-npc.sh update "[name]" "[what_happened]"
```

Examples: "insulted by party", "sold magic sword to Conan", "revealed location of temple"

### Quick NPC Personality Generator
If NPC has no established personality, roll or pick:

**Attitude (d6):** 1-2 Friendly, 3-4 Neutral, 5-6 Unfriendly

**Trait (d6):** 1 Nervous, 2 Gruff, 3 Cheerful, 4 Suspicious, 5 Helpful, 6 Tired

**Conversation Enders:** "I should get back to work" · "That's all I know" · "Good luck with that" · *Returns to previous activity* · "We're done here"

### Dialogue Patterns

**Information Request:** "What do you know about X?"
1. Would NPC know? (background/location) 2. Would they tell? (attitude) 3. Roll Persuasion if reluctant 4. Provide info based on result

**Transaction:** "I want to buy/sell X"
1. NPC deals in such items? 2. State base price 3. Persuasion DC 15 for discount 4. **PERSIST BEFORE NARRATING** (gold/inventory commands) 5. Narrate completed transaction

**Quest Offer:** "Do you need help?"
1. Check NPC situation 2. Determine if they have problems 3. Offer quest if appropriate 4. Add consequence for completion/failure

### Phase 5: Consequences
```bash
# Positive: NPC might help later
bash tools/dm-consequence.sh add "[NPC] assists party" "next meeting"

# Negative: NPC might hinder later
bash tools/dm-consequence.sh add "[NPC] spreads rumors" "next day"

# Information gained
bash tools/dm-note.sh "npc_info" "[NPC] revealed [information]"
```

---
