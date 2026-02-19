## State Persistence

**THE RULE**: If it happened, persist it BEFORE describing it to the player.

### Commands (Legacy, Still Supported)

| Change Type | Command |
|-------------|---------|
| Gold | `bash tools/dm-player.sh gold "[name]" [+/-amount]` |
| Item gained | `bash tools/dm-player.sh inventory "[name]" add "[item]"` |
| Item lost | `bash tools/dm-player.sh inventory "[name]" remove "[item]"` |
| HP changed | `bash tools/dm-player.sh hp "[name]" [+/-amount]` |
| XP earned | `bash tools/dm-player.sh xp "[name]" +[amount]` |
| Condition added | `bash tools/dm-condition.sh add "[name]" "[condition]"` |
| Condition removed | `bash tools/dm-condition.sh remove "[name]" "[condition]"` |
| Check conditions | `bash tools/dm-condition.sh check "[name]"` |
| NPC updated | `bash tools/dm-npc.sh update "[name]" "[event]"` |
| Location moved | `bash tools/dm-session.sh move "[location]"` |
| Future event (timed) | `bash tools/dm-consequence.sh add "[event]" "[label]" --hours N` |
| Future event (manual) | `bash tools/dm-consequence.sh add "[event]" "[trigger text]"` |
| Advance time consequences | `bash tools/dm-consequence.sh tick N` (N = hours elapsed) |
| Important fact | `bash tools/dm-note.sh "[category]" "[fact]"` |
| Party NPC HP | `bash tools/dm-npc.sh hp "[name]" [+/-amount]` |
| Party NPC condition | `bash tools/dm-npc.sh condition "[name]" add "[cond]"` |
| Party NPC equipped | `bash tools/dm-npc.sh equip "[name]" "[item]"` |
| NPC joins party | `bash tools/dm-npc.sh promote "[name]"` |
| Tag NPC to location | `bash tools/dm-npc.sh tag-location "[name]" "[location]"` |
| Tag NPC to quest | `bash tools/dm-npc.sh tag-quest "[name]" "[quest]"` |
| **Custom stat changed** | `bash tools/dm-player.sh custom-stat "[name]" "[stat]" [+/-amount]` |

### Note Categories
- `session_events` - What happened this session
- `plot_local` - Local storyline developments
- `plot_regional` - Broader mystery/conspiracy
- `plot_world` - Major world-shaking revelations
- `player_choices` - Key decisions and reasoning
- `npc_relations` - How NPCs feel about the party

---
