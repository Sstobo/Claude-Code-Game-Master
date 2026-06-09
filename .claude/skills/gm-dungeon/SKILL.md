---
name: gm-dungeon
description: Dungeon exploration — lightweight (narrative, default) vs structured (per-room JSON) modes, exit/obstacle handling, and ASCII map symbols. Load when the party enters a cave, ruin, or underground complex.
---

# Dungeon Exploration

| Mode | Best for |
|------|----------|
| **Lightweight** (default) | Fast, narrative; one master location entry with `internal_layout` + `areas_visited` |
| **Structured** | Tactical/revisited 3+ times; separate location per room with a `dungeon` field + `exits` + `state` |

## Lightweight flow
Enter → describe entrance + visible exits → explore (draw a map only when tactically useful, not every room) → combat by zone → on exit update master notes if significant.

## Structured flow
Validate exit (exists? locked/secret?) → handle obstacle (pick/force/key; find secret via Perception) → set destination discovered/visited → `gm-session.sh move "[Dungeon - Room]"` → describe (2-4 sentences) + list exits + creatures.

## Reward an exploration win (award spectacle XP)
An exploration breakthrough EARNS progress like a kill — disarming a deadly trap, finding the secret way, a daring escape, navigating a punishing hazard, an environmental kill. Persist before narrating: `bash tools/gm-player.sh award --tier minor|major|legendary --reason "..."` (kit-aware, level-scaled, co-awards followers in DCC). See `gm-craft → Reward the spectacle`.

## ASCII map symbols
`@` current · `+` door · `#` locked door · `△` stairs up · `▽` stairs down · `~` secret (found) · `▓` fog of war.
