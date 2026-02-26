## Dungeon Exploration

### Two Modes

| Mode | Best For | When to Use |
|------|----------|-------------|
| **Lightweight** (Default) | Fast-paced, narrative-focused | Most dungeons |
| **Structured** (Optional) | Tactical puzzles, revisitable | Complex dungeons, 3+ revisits |

### Lightweight Mode (Default)

Keep dungeon details in a single master location entry:

```json
{
  "The Laughing Crypt": {
    "position": "Beneath the ruins",
    "description": "A two-level crypt...",
    "internal_layout": "UPPER: Entry chamber → DOWN: Pit. EAST: Alcove.",
    "current_area": "Entry chamber",
    "areas_visited": ["Entry chamber"],
    "notes": "Grimaldi regenerating below."
  }
}
```

Draw ASCII maps **inline** when tactically useful (not every room).

### Lightweight Flow
```
1. ENTER - Describe entrance, mention visible exits, no JSON needed
2. EXPLORE - Narrate each area, draw map only when tactically useful
3. COMBAT - Note which "zone" enemies are in, describe movement narratively
4. EXIT - Update master location notes if significant, log discoveries
```

### When to Draw Maps
- Complex multi-path decisions
- Combat with positioning across zones
- Player asks for spatial clarity
- **NOT every room transition** - keep pacing snappy

### Structured Mode (When Needed)

Separate location per room with `dungeon` field:

```json
{
  "Goblin Caves - Guard Room": {
    "dungeon": "Goblin Caves",
    "room_number": 2,
    "exits": {
      "north": { "to": "Chieftain's Chamber", "type": "door", "locked": true },
      "south": { "to": "Entry Hall", "type": "open" },
      "east": { "to": "Hidden Treasury", "type": "secret", "dc": 16, "found": false }
    },
    "state": { "discovered": true, "visited": true, "cleared": false }
  }
}
```

### Structured Flow
```
1. VALIDATE EXIT - Does it exist? Blocked/locked? Secret unfound?
2. HANDLE OBSTACLES - Locked: pick/force/key. Secret: find first (Perception)
3. CREATE LOCATION - If new room, create it first:
   bash tools/dm-location.sh add "[Dungeon Room Name]" "[description]"
   bash tools/dm-location.sh connect "[current]" "[new_room]" --terrain [type] --distance [meters]
4. PERSIST - bash tools/dm-session.sh move "[Dungeon Room Name]"
5. SHOW ROOM - Describe (2-4 sentences), list exits with types, note creatures
```

**IMPORTANT:** For dungeon rooms, ALWAYS create location + connection manually BEFORE moving. `dm-session.sh move` does NOT auto-create dungeons.

**Use Structured when:** Revisited 3+ times, complex puzzle states, player wants tactical grid play

### ASCII Map Symbols
```
@ = Current position    + = Door        # = Locked door
△ = Stairs up          ▽ = Stairs down  ~ = Secret (found)
▓ = Fog of war (undiscovered)
```

### Dungeon Room Display Format
```
================================================================
  DUNGEON: Goblin Caves                    ROOM 2: Guard Room
  ────────────────────────────────────────────────────────────
  HP: ████████░░░░ 18/24   │  XP: 340  │  GP: 27
================================================================

  Torchlight reveals a cramped chamber. An overturned table
  and scattered bones suggest a hasty departure.

  EXITS: North (door, locked) · South (passage) · East (wall?)

  [A]ttack goblins  [S]earch room  [B]ack south

================================================================
```

---
