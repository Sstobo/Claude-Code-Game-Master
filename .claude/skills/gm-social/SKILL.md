---
name: gm-social
description: Social / NPC interaction workflow — load NPC context, attitude check, social mechanics (Persuasion/Deception/Intimidation/Insight DCs), and persisting NPC memory + consequences. Load whenever the player talks to, persuades, or reads an NPC ("I talk to...", "I ask...").
---

# Social / NPC Interaction

The DCs below are 5e — use them only when the scene-context KIT block says `dnd5e`.

## 1. Load NPC context
`bash tools/gm-context.sh "[npc]"` + `bash tools/gm-npc.sh status "[name]"`. Surface the NPC's `goal`, `current_mood`, secret-EXISTENCE (never the text), `bonds`, and `voice` (`gm-npc.sh voice`). Check prior interactions + active quests.

## 1b. Flesh a stub on first real contact
Present NPCs correctly START as one-line stubs (a play-pack "Present in ..." blurb, no `goal`/`secret`/`voice`) — that is the anti-gazetteer rule, not a bug. But the moment the player **meaningfully engages** one (talks to them, presses them, reads them), give them an interior so nobody the player actually talks to stays a "neutral stub": author a **want**, a **secret**, and how they **sound**, and persist it in one call —
```bash
bash tools/gm-npc.sh set-inner "[name]" --goal "[what they want]" --secret "[what they hide]" --voice "[how they sound]"
```
Only on real contact — do not pre-flesh NPCs the player never engages. Once set, it rides into every future scene they're in (mood/goal/secret-existence + their remembered `events`).

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
Positive (NPC helps later) / negative (NPC hinders) → `bash tools/gm-consequence.sh add "[event]" "[trigger]" [--trigger-type on_npc --match "[name]"]`. **Mandatory** whenever the interaction leaves ongoing fallout — a failed ask that changes how this NPC treats you later is exactly that.

## Failure — the ask is DENIED and it costs (see `gm-skills → Failure consequences`)
Decide before rolling what refusal COSTS (never tell the player). On a failed social check:
- **The ask does not happen.** Don't refund the stake by ending on a softer re-ask that costs nothing. If the NPC leaves a door open, that's escalation the fiction has to price — new leverage, new information, or something the player gives up.
- **Whatever was on the table is spent.** If the player was bargaining for lives, cargo, passage, or mercy, the failure is where that thing is lost — not deferred. The NPC responds from their own goals and power; sometimes that's ugly.
- **Persist the shift** so refusals compound like wins do: `bash tools/gm-npc.sh mood "[name]" "[new mood]"` + `gm-npc.sh set-inner` (goal/attitude), and `gm-npc.sh update "[name]" "[what happened]"`.

## Reward a social win (award spectacle XP)
A real social victory — a hard persuasion landed, a daring bluff, turning a hostile NPC, talking your way past a threat — EARNS progress like a kill. Persist it before the payoff: `bash tools/gm-player.sh award --tier minor|major|legendary --reason "..."` (kit-aware, level-scaled, co-awards followers in DCC). See `gm-craft → Reward the spectacle`.

## Craft (see gm-craft)
NPCs have agendas, not quests. Don't over-share — secrets revealed slowly are 10x better. NPCs can say no, lie, or give bad advice. End with a conversation-ender if they're done.
