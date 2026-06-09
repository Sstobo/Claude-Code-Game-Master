---
name: gm-social
description: Social / NPC interaction workflow — load NPC context, attitude check, social mechanics (Persuasion/Deception/Intimidation/Insight DCs), and persisting NPC memory + consequences. Load whenever the player talks to, persuades, or reads an NPC ("I talk to...", "I ask...").
---

# Social / NPC Interaction

## 1. Load NPC context
`bash tools/gm-context.sh "[npc]"` + `bash tools/gm-npc.sh status "[name]"`. Surface the NPC's `goal`, `current_mood`, secret-EXISTENCE (never the text), `bonds`, and `voice` (`gm-npc.sh voice`). Check prior interactions + active quests.

## 2. Attitude
Friendly (helpful, warm) · Neutral (professional, cautious) · Hostile (dismissive, cold). Derive from history + bonds.

## 3. Social mechanics — when to roll
| Skill | DC (Friendly / Neutral / Hostile) | Use |
|-------|-----------------------------------|-----|
| Persuasion | 10 / 15 / 20 | Change their mind |
| Deception | 10 / 15 / 20 (plausible→outrageous) | Hide truth |
| Intimidation | 10 / 15 / 20 (weak→strong-willed) | Force compliance |
| Insight | opposed vs Deception, or DC 10-20 | Read them |

Modifiers: unreasonable request +5 DC; good rapport -2 DC.
**No roll needed:** public info, normal commerce at listed prices, casual talk, giving things freely.

## 4. Persist NPC memory
`bash tools/gm-npc.sh update "[name]" "[what happened]"` and `bash tools/gm-npc.sh mood "[name]" "[new mood]"` — reactions compound across sessions.

## 5. Consequences
Positive (NPC helps later) / negative (NPC hinders) → `bash tools/gm-consequence.sh add "[event]" "[trigger]" [--trigger-type on_npc --match "[name]"]`.

## Reward a social win (award spectacle XP)
A real social victory — a hard persuasion landed, a daring bluff, turning a hostile NPC, talking your way past a threat — EARNS progress like a kill. Persist it before the payoff: `bash tools/gm-player.sh award --tier minor|major|legendary --reason "..."` (kit-aware, level-scaled, co-awards followers in DCC). See `gm-craft → Reward the spectacle`.

## Craft (see gm-craft)
NPCs have agendas, not quests. Don't over-share — secrets revealed slowly are 10x better. NPCs can say no, lie, or give bad advice. End with a conversation-ender if they're done.
