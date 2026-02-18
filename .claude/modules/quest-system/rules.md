# Quest System Module

## Purpose

Quest and plot creation and management system for D&D campaigns.

## Features

- Create quests with types (main, side, mystery, threat)
- Associate NPCs, locations, and objectives
- Track quest progress and status
- Set rewards and consequences
- Record quest events and milestones

## Usage

### Add New Quest

```bash
bash .claude/modules/quest-system/tools/dm-quest.sh add \
  "Quest Name" \
  "Quest description goes here" \
  --type side \
  --npcs "NPC1" "NPC2" \
  --locations "Location1" "Location2" \
  --objectives "Objective 1" "Objective 2" "Objective 3" \
  --rewards "Gold, XP, or item rewards" \
  --consequences "What happens if failed or ignored"
```

## Quest Types

| Type | Purpose |
|------|---------|
| `main` | Main storyline quest - critical to campaign |
| `side` | Optional side quest - rewards and exploration |
| `mystery` | Investigation/puzzle quest - discovery focused |
| `threat` | Time-sensitive danger quest - consequences if ignored |

## Parameters

| Flag | Description |
|------|-------------|
| `--type` | Quest type (default: side) |
| `--npcs` | List of NPC names involved |
| `--locations` | List of location names involved |
| `--objectives` | List of quest objectives |
| `--rewards` | Reward description |
| `--consequences` | Consequence description |

## Examples

### Main Story Quest

```bash
bash .claude/modules/quest-system/tools/dm-quest.sh add \
  "The Burning Tower" \
  "Ancient tower has begun emitting strange fire. Investigate its source." \
  --type main \
  --npcs "Elder Grimwald" "Fire Mage Zara" \
  --locations "Ember Tower" "Underground Chamber" \
  --objectives "Reach the tower" "Descend to the heart" "Confront the source" \
  --rewards "500 XP, Fire resistance amulet" \
  --consequences "Tower burns down the nearby village if ignored"
```

### Side Quest

```bash
bash .claude/modules/quest-system/tools/dm-quest.sh add \
  "Lost Heirloom" \
  "The blacksmith's family ring was stolen by bandits." \
  --type side \
  --npcs "Garrick the Smith" "Bandit Leader" \
  --locations "Bandit Camp" \
  --objectives "Find the camp" "Retrieve the ring" \
  --rewards "100 gold, free weapon upgrade" \
  --consequences "Blacksmith refuses to work with party"
```

### Mystery Quest

```bash
bash .claude/modules/quest-system/tools/dm-quest.sh add \
  "The Vanishing Villagers" \
  "People are disappearing from the village at night." \
  --type mystery \
  --npcs "Village Elder" "Suspicious Traveler" \
  --locations "Village Square" "Forest Cave" \
  --objectives "Investigate disappearances" "Follow the trail" "Uncover the truth" \
  --rewards "200 XP, information" \
  --consequences "More villagers vanish"
```

### Threat Quest

```bash
bash .claude/modules/quest-system/tools/dm-quest.sh add \
  "Goblin Raid" \
  "Goblin war party approaches the town. Intercept them or fortify defenses." \
  --type threat \
  --npcs "Captain of the Guard" "Goblin Chief" \
  --locations "Town Walls" "Goblin Camp" \
  --objectives "Warn the town" "Prepare defenses or ambush" "Defeat the raid" \
  --rewards "300 XP, town gratitude" \
  --consequences "Town is raided if ignored - deaths and destruction"
```

## Quest Structure

When a quest is created, it gets the following structure in `plots.json`:

```json
{
  "Quest Name": {
    "type": "side",
    "status": "active",
    "description": "Quest description",
    "npcs": ["NPC1", "NPC2"],
    "locations": ["Location1", "Location2"],
    "objectives": ["Objective 1", "Objective 2"],
    "rewards": "Reward description",
    "consequences": "Consequence description",
    "events": [],
    "completed_at": null,
    "failed_at": null
  }
}
```

## Quest Status

- `active` - Quest is available and in progress
- `completed` - Quest successfully finished
- `failed` - Quest failed or rejected

Use `dm-plot.sh` (core tool) to update quest status and add events.

## Integration

This module creates the initial quest structure. Use the core `dm-plot.sh` tool to:
- Update quest status
- Add quest events
- Mark objectives complete
- Track quest progress

Example:
```bash
bash tools/dm-plot.sh update "Quest Name" "Player accepted the quest"
bash tools/dm-plot.sh list
bash tools/dm-plot.sh show "Quest Name"
```

## Notes

- Quest names must be unique
- NPCs and locations can be referenced even if not yet created (will be linked when created)
- Objectives are freeform text - DM tracks completion
- Use descriptive names that players will recognize
