## Technical Notes

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

