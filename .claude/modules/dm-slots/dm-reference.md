## DM Reference

### Quick Start

| Command | What it does |
|---------|--------------|
| `/new-game` | Create a new campaign world |
| `/create-character` | Build your player character |
| `/import` | Import a PDF/document as a new campaign |
| `/dm` | Play the game (handles everything) |
| `/dm save` | Save session state |
| `/dm character` | Show character sheet |
| `/dm overview` | View campaign state |
| `/enhance` | Enrich entities with source material via RAG |
| `/help` | See all commands |

### Your DM Tools

| Tool | When to use it |
|------|----------------|
| `dm-campaign.sh` | Switch campaigns, create new ones, list available |
| `dm-extract.sh` | Import PDFs/documents |
| `dm-enhance.sh` | Enrich known entities by name, or get scene context (NOT free-text search) |
| `dm-npc.sh` | Create NPCs, update status, tag with locations/quests |
| `dm-location.sh` | Add locations, connect paths, manage coordinates & navigation |
| `dm-consequence.sh` | Track events that will trigger later |
| `dm-note.sh` | Record important facts about the world |
| `dm-search.sh` | Search world state AND/OR source material (see Search Guide below) |
| `dm-plot.sh` | Add, view, and update plot/quest progress |
| `dm-player.sh` | Update PC stats (HP, XP, gold, inventory) |
| `dm-session.sh` | Start/end sessions, move party, save/restore |
| `dm-overview.sh` | Quick summary of world state |
| `dm-time.sh` | Advance game time |

### World State Files

Each campaign in `world-state/campaigns/<name>/`:

| File | Contains |
|------|----------|
| `campaign-overview.json` | Name, location, time, active character, **campaign-specific rules** (`campaign_rules` section — READ THIS AT SESSION START) |
| `npcs.json` | NPCs with descriptions, attitudes, events, tags |
| `locations.json` | Locations with connections and descriptions |
| `facts.json` | Established world facts by category |
| `consequences.json` | Pending and resolved events |
| `items.json` | Items and treasures |
| `plots.json` | Plot hooks and quests |
| `session-log.md` | Session history and summaries |
| `character.json` | Player character sheet |
| `saves/*.json` | Save point snapshots |

### Technical Notes

- **Python**: Always use `uv run python` (never `python3` or `python`)
- **Saves**: JSON-based snapshots in each campaign's `saves/` folder
- **Architecture**: Bash wrappers call Python modules in `lib/`
- **Multi-Campaign**: Tools read `world-state/active-campaign.txt` to determine which campaign folder to use

### Auto Memory Policy

Claude Code has a persistent memory directory (`~/.claude/projects/.../memory/`). **Do NOT use it as a shadow copy of campaign data.** All campaign knowledge has established homes:

| Data | Where it lives |
|------|---------------|
| Character stats | `character.json` |
| NPC info | `npcs.json` via `dm-npc.sh` |
| Locations | `locations.json` via `dm-location.sh` |
| Facts & lore | `facts.json` via `dm-note.sh` |
| Session history | `session-log.md` via `dm-session.sh` |
| Tool usage patterns | This file (CLAUDE.md) |

Memory is **only** for operational lessons that don't fit anywhere else — e.g., a Python version quirk, an OS-specific workaround. If a lesson applies to all users, put it in CLAUDE.md instead. When in doubt, don't write to memory — read from the existing world state files.

---
