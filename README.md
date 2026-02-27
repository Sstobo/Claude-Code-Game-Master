# DM Claude — AI Dungeon Master

**Drop any book into it. Play inside the story.**

Got a favourite fantasy novel? A Star Trek fanfic? A weird detective novel from the 70s? Drop the PDF in — the system extracts every character, location, item, and plot thread, then drops you into that world as whoever you want to be.

D&D 5e rules give the story stakes and consequences. You don't need to know D&D. Just say what you want to do.

---

## Getting Started

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

```bash
git clone https://github.com/Sstobo/Claude-Code-Game-Master.git
cd Claude-Code-Game-Master
./install.sh
```

Once installed:

1: Optional: drop a PDF or text file into `source-material/`
2. Run `claude` to launch Claude Code
3. Type `/new-game` — choose **Classic** for the classic experience, or if youre feeling brave, **Advanced** to configure modules 

---

## Two Modes: Classic and Advanced

When you run `/new-game`, the first choice you make is the mode for that campaign. It's set once and lives with the campaign forever.

### Classic (default)

The original experience. Zero setup beyond naming your campaign.

- Standard D&D 5e mechanics
- Full world generation, NPCs, locations, plot hooks, consequences
- Source material import (RAG-powered — play inside any book)
- Save/restore, session history, character sheets
- Works immediately out of the box

### Advanced (opt-in per campaign)

Everything in Classic, plus a suite of optional modules you toggle like game mods. Designed for campaigns that need mechanics beyond standard D&D.

At campaign creation you get a module selection menu, narrator style picker, and campaign rules template selector. All of it lives in `.claude/modules/` and never touches the vanilla core.

---

## Advanced Modules

| Module | What it does | Good for |
|--------|-------------|----------|
| 🌍 **world-travel** | Spatial world simulation: real XY coordinates, A\* pathfinding, travel time by distance + speed. Auto-runs encounter checks on move. ASCII map, minimap, GUI. | Any campaign with a real map |
| 🎭 **custom-stats** | Any custom stat — mana, sanity, hunger, radiation, reputation. Per-hour decay/gain, conditional effects, per-tick simulation. Zero hardcoded names. | STALKER, Fallout, survival horror |
| ⚔️ **firearms-combat** | Automated combat resolver. RPM → shots per round, fire modes (single/burst/full\_auto), PEN vs PROT damage scaling, subclass bonuses. | Modern or military campaigns |
| 📦 **inventory-system** | Atomic multi-change transactions (`--gold --hp --xp --add --remove` in one command). Stackable items with quantities. Unique items with automatic validation. | All campaigns |

Each module is self-contained: its own `tools/`, `lib/`, `rules.md`, and `module.json`. Drop a folder into `.claude/modules/` to install community modules.

---

## Campaign Ideas

The system is universal — not just fantasy.

| Campaign | You play as... |
|----------|---------------|
| **S.T.A.L.K.E.R.** | A stalker in the Chernobyl Zone. Radiation, anomalies, mutants, rival factions. Hunger and thirst tick in real time. |
| **Fallout** | A vault dweller emerging into a post-nuclear wasteland. SPECIAL stats, bottlecaps, power armor. |
| **Metro 2033** | A survivor in Moscow's metro tunnels. Factions at war, mutants on the surface, bullets as currency. |
| **Civilization** | An immortal ruler guiding a civilization from stone age to space age. Strategic decisions across millennia. |
| **SCP: Infinite IKEA** | Trapped inside SCP-3008 — an infinite IKEA. Friendly by day, predatory staff by night. No exit. |
| **Star Wars: Clone Wars** | A clone trooper squad leader or Jedi on tactical missions during the Clone Wars. |
| **Warhammer 40K** | An Imperial Guard soldier in the grim far future. Everything wants to kill you. Everything will. |
| **Pirates of the Caribbean** | A pirate captain in the 1700s. Treasure, naval battles, supernatural curses. |
| **Medieval Child** | An orphaned child in war-torn medieval Europe. No combat stats — just stealth, cunning, and cold. |
| **Barotrauma** | A submarine crew on an alien ocean moon. Pressure, monsters, and things going very wrong with the hull. |

---

## In Action — Dungeon Crawler Carl

A campaign imported from *Dungeon Crawler Carl*. Tandy the sasquatch rips the skin off a Terror Clown, forces Carl to wear it as a disguise, then performs a sasquatch mating dance to distract Grimaldi while Donut frees the dragon.

![Tandy acquires Terror Clown skin disguise for Carl](public/622422010_1572097020675669_3114747955156903860_n.png)

![Tandy performs a sasquatch mating dance to distract Grimaldi](public/625560066_33916991331281718_1129121114640091251_n.png)

![Exploring The Laughing Crypt — thirty clown bodies wake up](public/623940676_2000130920531570_2521032782764513297_n.png)

---


## How It Works

When you import a document, the system vectorizes it with ChromaDB and spawns extraction agents that pull the book apart into structured data. During gameplay, every scene gets grounded in real passages from your source material.

Everything persists. NPCs remember what you said last session. Consequences fire days later in-game time. Locations change as events unfold. Save and restore at any point.

Specialist agents spin up on the fly — monster stats, spell mechanics, loot tables, equipment databases. The player sees only the story. It uses the [D&D 5e API](https://www.dnd5eapi.co/) for official rules, spellbooks, monsters, and equipment.

---

## Commands

| Command | What it does |
|---------|--------------|
| `/dm` | Start or continue your story |
| `/dm save` | Save your progress |
| `/dm character` | View your character sheet |
| `/dm overview` | See the world state |
| `/new-game` | Create a world from scratch (choose Classic or Advanced) |
| `/create-character` | Build your character |
| `/import` | Import a PDF/document as a campaign |
| `/enhance` | Enrich entities with source material |
| `/help` | Full command reference |

---

## Core Tools

| Tool | Purpose |
|------|---------|
| `dm-campaign.sh` | Create, list, switch campaigns |
| `dm-session.sh` | Session lifecycle, movement, save/restore |
| `dm-player.sh` | HP, XP, gold, inventory, conditions |
| `dm-npc.sh` | NPC creation, updates, party management |
| `dm-location.sh` | Locations and connections |
| `dm-time.sh` | Update in-game time |
| `dm-consequence.sh` | Schedule and resolve consequences |
| `dm-plot.sh` | Quest and storyline tracking |
| `dm-search.sh` | Search world state and source material |
| `dm-enhance.sh` | RAG-powered entity enrichment |
| `dm-extract.sh` | Document import pipeline |
| `dm-note.sh` | Record world facts |
| `dm-overview.sh` | World state summary |

Advanced module tools (`dm-inventory.sh`, `dm-combat.sh`, `dm-map.sh`, `dm-encounter.sh`, `dm-navigation.sh`, `dm-vehicle.sh`, `dm-survival.sh`) are available when the relevant module is enabled for a campaign.

---

## Specialist Agents

| Agent | Triggered by |
|-------|--------------|
| `monster-manual` | Combat encounters |
| `spell-caster` | Casting spells |
| `rules-master` | Mechanical edge cases |
| `gear-master` | Shopping, identifying gear |
| `loot-dropper` | Victory, treasure discovery |
| `npc-builder` | Meeting new NPCs |
| `world-builder` | Exploring new areas |
| `dungeon-architect` | Entering dungeons |
| `create-character` | New characters |

---

## Architecture

```
CORE (vanilla)                   ADVANCED (opt-in, per campaign)
──────────────                   ───────────────────────────────
lib/                             .claude/modules/
tools/                             ├── infrastructure/   ← dispatch, narrator, rules
.claude/commands/                  ├── custom-stats/
                                   ├── world-travel/
                                   ├── inventory-system/
                                   └── firearms-combat/
```

The vanilla core (`lib/`, `tools/`) is never modified by modules. Advanced features hook in via middleware — enabled per campaign, invisible when not active. A campaign's `advanced_mode` flag in `campaign-overview.json` determines which path `/dm` takes.

---

## License

This work is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — free to share and adapt for non-commercial use. See [LICENSE](LICENSE) for details.

---

Original project by [Sean Stobo](https://www.linkedin.com/in/sean-stobo/). Advanced modules contributed by [Maxim Astrakhantsev](https://www.linkedin.com/in/maxim-astrakhantsev-13a9391b9/).

Your story awaits. Run `/new-game` to begin.
