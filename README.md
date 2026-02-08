# DM Claude

**Step inside your favorite books and live the story.**

Import any novel, adventure module, or world guide — DM Claude extracts the characters, locations, plots, and lore, then lets you explore that world as a D&D 5e adventure. Your choices matter. NPCs remember you. The story adapts.

---

## Getting Started

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and Python 3.11+

```bash
git clone https://github.com/Sstobo/Claude-Code-Game-Master.git && cd Claude-Code-Game-Master && claude
```

1. Ask the agent to set up dependencies
2. Once it's done, drop a PDF in the `source-material/` folder
3. Run `/dm` and let the agent guide you

That's it. The AI handles installation, world extraction, character creation, and gameplay.

---

## Commands

| Command | What it does |
|---------|--------------|
| `/dm` | Start or continue your story |
| `/dm save` | Save your progress |
| `/dm character` | View your character sheet |
| `/dm overview` | See the world state |
| `/new-game` | Create a world from scratch |
| `/create-character` | Build your character |
| `/import` | Import a PDF/document as a new campaign |
| `/enhance` | Enrich entities with source material via RAG |
| `/help` | Full command reference |

---

## How It Works

**Import** — Drop a PDF, EPUB, or text file into `source-material/`. The extraction system parses it using concurrent specialist agents to identify NPCs, locations, items, and plot threads. Everything is vectorized for RAG retrieval during gameplay.

**Play** — Describe what you want to do. The AI narrates the world's response, pulling relevant passages from your source material to stay faithful to the original while adapting to your choices. Combat, social encounters, exploration, and skill checks all follow D&D 5e rules with real dice rolls. You don't need to know D&D — just describe your intent.

**Persist** — Everything is remembered. NPC attitudes shift, locations change, consequences trigger on timers, quests track progress, and your character grows. Save points let you checkpoint and restore at any time.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

*Your story awaits. Run `/dm` to begin.*
