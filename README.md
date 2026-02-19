[🇷🇺 Читать на русском](README.ru.md)

# DM Claude — Enhanced Fork

> **Fork of [Sstobo/Claude-Code-Game-Master](https://github.com/Sstobo/Claude-Code-Game-Master)** with a modular architecture — toggle optional systems (survival stats, firearms, encounters, navigation) per campaign like game mods.

**Drop any book into it. Play inside the story.** Got a favorite fantasy novel? A STALKER fanfic? A weird sci-fi book from the 70s? Drop the PDF in, and DM Claude extracts every character, location, item, and plot thread, then drops you into that world as whoever you want to be.

D&D 5e rules give the story stakes and consequences. You don't need to know D&D — just say what you want to do.

---

## Modules

Optional systems enabled per campaign. At creation `/dm` scans all available modules and presents them as a mod selection menu — pick what fits your setting, the DM patches the config automatically.

| Module | What it does | Good for |
|--------|-------------|----------|
| 🌍 **world-travel** | Spatial world simulation: real XY coordinates, A* pathfinding, travel time by distance + speed. Auto-runs encounter checks on move. ASCII map, minimap, GUI. Add locations by bearing and distance. | Any campaign with a real map and travel |
| 🎭 **custom-stats** | Any custom stat — mana, sanity, oxygen, reputation, hunger, radiation, whatever. Per-hour decay/gain, conditional effects (artifact heals only when wounded), per-tick simulation. Zero hardcoded names. | STALKER, Fallout, survival horror, fantasy |
| ⚔️ **firearms-combat** | Automated combat resolver. RPM → shots per round, fire modes (single/burst/full_auto), PEN vs PROT scaling, subclass bonuses. Pre-built template with AKM/AK-74/M4A1/SVD. | Any modern/military campaign |
| 📦 **inventory-system** | Atomic multi-change transactions (`--gold --hp --xp --add --remove` in one command). Stackable items with quantities. Unique items (weapons, armor). `--test` mode. | All campaigns (recommended always) |

Each module is self-contained: own `tools/`, `lib/`, `rules.md`, `module.json`. Drop a folder into `.claude/modules/` to install a community module.

---

## What's New in This Fork

### 🧩 Module System — Campaign Mods
When creating a new campaign, `/dm` scans all available modules and presents them as optional mods. Pick what you want, the DM enables them and patches the campaign config automatically.

```
================================================================
  OPTIONAL MODS
  ────────────────────────────────────────────────────────────
  [1] World Travel         — spatial map, distances, travel time + encounters
  [2] Custom Stats         — any stat (hunger, sanity, mana) decay over time
  [3] Firearms Combat      — modern weapons, fire modes, PEN/PROT
  [4] Inventory System     — atomic transactions, stackable/unique items
  [A] Enable ALL
  [N] None — standard D&D only
================================================================
```

Each module is self-contained: own tools, rules, and config patches. Add community modules by dropping a folder into `.claude/modules/`.

### 🔀 Middleware Architecture
CORE tools (`dm-time.sh`, `dm-player.sh`, `dm-session.sh`, etc.) are vanilla upstream. Modules hook in via middleware — no CORE modifications needed. `/dm` automatically injects all active module rules into context.

### 🌍 World Travel Module
`coordinate-navigation` and `encounter-system` merged into a single `world-travel` module. Install one module, get everything: spatial coordinates, A* pathfinding, travel time calculation, and automatic encounter checks on every move.

```bash
bash tools/dm-session.sh move "Ruins"
# Auto: calculates distance → ticks time → runs encounter check → applies custom stat effects
```

### ⏱️ Time Tracking & Timed Consequences
`dm-time.sh` now tracks total elapsed hours across the campaign. Consequences can be set to trigger after a number of hours — `tick` decrements the counter on every time advance, fires when it hits zero.

```bash
bash tools/dm-time.sh advance 4 --elapsed
# Stores total_hours_elapsed, auto-ticks all timed consequences

bash tools/dm-consequence.sh add "Trader arrives" "24h" --hours 24
bash tools/dm-consequence.sh tick 4
# Shows: "Trader arrives (20.0h)" → ... → "IMMINENT!"
```

### 📜 Plot Add in CORE
`add_plot()` promoted from `quest-system` module to vanilla CORE. No module required — `dm-plot.sh add` works in any campaign.

```bash
bash tools/dm-plot.sh add "The Lost Relic" --type side --description "..."
```

### 🎯 Unified Inventory Manager
Atomic transaction system for character state — apply multiple changes at once or none at all. Stackable items (consumables with quantities) and unique items (weapons, armor, quest items) with automatic validation and rollback.

```bash
# Atomic transaction — all changes succeed or fail together
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "Character" \
  --gold +150 \
  --xp +200 \
  --hp -10 \
  --add "Medkit" 2 "Ammo 9mm" 30 \
  --add-unique "AK-47 (7.62x39mm, 2d8+3, PEN 4)" \
  --remove "Bandage" 1 \
  --custom-stat hunger +20

# Test mode — validate without applying
bash .claude/modules/inventory-system/tools/dm-inventory.sh update "Character" --gold -500 --test
```

**Auto-migrates** from old inventory format on first use (creates timestamped backup).

### ⚔️ Automated Firearms Combat
Resolve modern firearms combat with realistic mechanics — RPM-based rounds per turn, fire modes (single/burst/full_auto), progressive attack penalties, and PEN vs PROT damage scaling. Detailed shot-by-shot output with complete roll breakdowns.

```bash
bash .claude/modules/firearms-combat/tools/dm-combat.sh resolve \
  --attacker "Stalker" \
  --weapon "AKM" \
  --fire-mode "full_auto" \
  --ammo 60 \
  --targets "Mutant#1:AC14:HP30:PROT2" "Mutant#2:AC14:HP30:PROT2"

# Test mode — preview combat without updating state
bash .claude/modules/firearms-combat/tools/dm-combat.sh resolve ... --test
```

**Auto-persists** ammo consumption and XP awards. Accounts for class bonuses (e.g., Стрелок reduced penalties).

### 📦 Modern Firearms Campaign Template
Pre-built template (`.claude/modules/firearms-combat/templates/modern-firearms-campaign.json`) with weapons (AKM, AK-74, M4A1, SVD), armor types with PROT ratings, fire mode definitions, custom survival stats (hunger/thirst/radiation/sleep), time effects, and encounter system — ready for STALKER, Fallout, or Cyberpunk campaigns.

### Custom Character Stats
Define **any** stats for your campaign — hunger, thirst, radiation, morale, sanity, reputation — whatever fits your world. Fully universal, zero hardcoded stat names.

```bash
bash tools/dm-player.sh custom-stat hunger +15
bash tools/dm-player.sh custom-stat radiation -5
```

### Time Effects Engine
Stats change automatically as game time passes. Define rates per hour in your campaign config, and the system handles the rest. Supports **conditional effects** (e.g., artifact healing only when HP < max) with per-tick simulation.

```
Time updated to: Evening (18:30), Day 3
Custom Stats:
  hunger: 80 → 68 (-12)
  thirst: 70 → 52 (-18)
⚠️ TRIGGERED: "Merchant arrives"
```

### Auto Movement Time
Move between locations and travel time is calculated automatically from distance and character speed. Custom stats tick during travel.

```bash
bash tools/dm-session.sh move "Ruins"
# Auto-calculates: 2000m at 4 km/h = 30 minutes
# Auto-applies time effects to hunger, thirst, etc.
```

### Timed Consequences
Schedule events that trigger after elapsed game time, not just on story beats. Time-remaining display shows minutes/hours/days left.

```bash
bash tools/dm-consequence.sh add "Trader arrives at camp" "in 24 hours" --hours 24
# Shows: "Trader arrives (12.5h left)" or "IMMINENT!"
```

### World Travel — Encounters + Navigation Combined
Configurable random encounters during travel — frequency scales with distance, time of day, and character stats. Encounters create waypoints on the map where you can fight, talk, or explore before continuing. Locations have real coordinates, A* pathfinding finds routes, view your world as ASCII maps or a GUI window.

```bash
bash tools/dm-session.sh move "Ruins"
# Auto-runs encounter check, calculates travel time, ticks stats

bash .claude/modules/world-travel/tools/dm-encounter.sh check "Village" "Ruins" 2000 open
bash .claude/modules/world-travel/tools/dm-map.sh              # Full ASCII map
bash .claude/modules/world-travel/tools/dm-map.sh --minimap    # Tactical minimap
bash .claude/modules/world-travel/tools/dm-map.sh --gui        # GUI window with terrain colors

# Add locations by bearing and distance
bash tools/dm-location.sh add "Outpost" "Abandoned outpost" \
  --from "Village" --bearing 90 --distance 2500 --terrain forest
```

### i18n Support
Cyrillic names, non-English attitudes, and Unicode identifiers work out of the box. Build campaigns in any language. All JSON saved with `ensure_ascii=False` — no more `\uXXXX` escaping.

---

## Campaign Ideas

The system is universal — not just fantasy. Here are some campaigns we've designed:

| Campaign | You play as... |
|----------|---------------|
| **S.T.A.L.K.E.R.** | A stalker in the Chernobyl Zone. Radiation, anomalies, mutants, rival factions. Hunger and thirst tick in real time. |
| **Fallout** | A vault dweller emerging into a post-nuclear wasteland. SPECIAL stats, bottlecaps, power armor. |
| **Metro 2033** | A survivor in Moscow's metro tunnels. Factions at war, mutants on the surface, bullets as currency. |
| **Civilization** | An immortal ruler guiding a civilization from stone age to space age. Strategic decisions across millennia. |
| **SCP: Infinite IKEA** | Trapped inside SCP-3008 — an infinite IKEA. Friendly by day, predatory staff by night. No exit. |
| **Star Wars: Clone Wars** | A clone trooper squad leader or Jedi on tactical missions during the Clone Wars. |
| **Warhammer 40K** | An Imperial Guard soldier in the grim far future. Everything wants to kill you. Everything will. |
| **RimWorld** | A colony manager on a frontier world. Raids, mental breaks, questionable survival ethics. |
| **Space Station 13** | A crewmember on a space station where everything goes wrong every 15 minutes. |
| **Pac-Man RPG** | A trapped soul in an endless maze, hunted by four ghosts with unique personalities. Yes, really. |
| **Ants vs Termites** | An ant commander leading colony wars across a backyard battlefield. Microscopic scale, epic stakes. |
| **Plague Inc (Reverse)** | An epidemiologist racing to stop a mutating pandemic while fighting bureaucracy and public denial. |
| **Inside a Computer** | A digital process inside a Russian server OS. Navigate file systems, fight viruses, avoid the kernel reaper. |
| **Medieval Child** | An orphaned child in war-torn medieval Europe. No combat stats — just stealth, cunning, and cold. |
| **Pirates of the Caribbean** | A pirate captain in the 1700s. Treasure, naval battles, supernatural curses. |
| **Barotrauma** | A submarine crew on an alien ocean moon. Pressure, monsters, and things going very wrong with the hull. |

All campaigns use the same engine. Custom stats, time effects, and encounters adapt to any setting.

---

## In Action — Dungeon Crawler Carl

A campaign imported from *Dungeon Crawler Carl*. Tandy the sasquatch rips the skin off a Terror Clown, forces Carl to wear it as a disguise, then performs a sasquatch mating dance to distract Grimaldi while Donut frees the dragon.

![Tandy acquires Terror Clown skin disguise for Carl](public/622422010_1572097020675669_3114747955156903860_n.png)

![Tandy performs a sasquatch mating dance to distract Grimaldi](public/625560066_33916991331281718_1129121114640091251_n.png)

![Exploring The Laughing Crypt — thirty clown bodies wake up](public/623940676_2000130920531570_2521032782764513297_n.png)

---

## Getting Started

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

```bash
git clone https://github.com/DrSeedon/Claude-Code-Game-Master.git
cd Claude-Code-Game-Master
./install.sh
```

Once installed:

1. Drop a PDF in the `source-material/` folder
2. Run `claude` to launch Claude Code
3. Run `/dm` and let the agent guide you

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
| `/new-game` | Create a world from scratch |
| `/create-character` | Build your character |
| `/import` | Import a PDF/document as a campaign |
| `/enhance` | Enrich entities with source material |
| `/help` | Full command reference |

## Tools

| Tool | Purpose |
|------|---------|
| `dm-campaign.sh` | Create, list, switch campaigns |
| `dm-session.sh` | Session lifecycle, movement, save/restore |
| `dm-player.sh` | HP, XP, gold, inventory, **custom stats** |
| **`dm-inventory.sh`** | **Unified inventory manager — atomic transactions, stackable/unique items** |
| **`dm-combat.sh`** | **Automated firearms combat resolver with PEN/PROT mechanics** |
| `dm-npc.sh` | NPC creation, updates, party management |
| `dm-location.sh` | Locations, connections, **coordinates, navigation** |
| `dm-time.sh` | Advance time, **time effects, precise time, conditional effects** |
| `dm-consequence.sh` | Event scheduling, **timed triggers with countdown** |
| `dm-encounter.sh` | **Random encounter checks** |
| `dm-map.sh` | **ASCII maps, minimap, GUI** |
| `dm-path.sh` | **A* pathfinding between locations** |
| `dm-plot.sh` | Quest and storyline tracking, **plot creation** |
| `dm-search.sh` | Search world state and source material |
| `dm-enhance.sh` | RAG-powered entity enrichment |
| `dm-extract.sh` | Document import pipeline |
| `dm-note.sh` | Record world facts |
| `dm-overview.sh` | World state summary |

**Bold** = new in this fork.

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

## Roadmap

Features planned for future releases:

- **Nested Sub-Maps** — locations can contain their own internal maps. Enter a castle and explore its floors. Board a spaceship and navigate its decks. Dive into a cave system with branching tunnels. Each sub-map connects back to the parent world map seamlessly.
- **Multi-Floor Dungeons** — vertical dungeon navigation with stairs, elevators, ladders between floors. Each floor is its own sub-map with independent room states.
- **Vehicle Interiors** — ships, airships, space stations as explorable sub-maps that move on the world map. The vehicle travels between locations while you explore inside it.
- **Inventory Weight & Slots** — carry capacity based on STR, overencumbrance penalties, automatic stacking, category filters. [See design in TODO.md](TODO.md)
- **Visual Map Export** — export ASCII maps to PNG/SVG for sharing outside the terminal.

Got ideas? [Open an issue](https://github.com/DrSeedon/Claude-Code-Game-Master/issues) or submit a PR.

---

## License

This work is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — free to share and adapt for non-commercial use. See [LICENSE](LICENSE) for details.

---

Original project by [Sean Stobo](https://www.linkedin.com/in/sean-stobo/). Fork enhanced by [Maxim Astrakhantsev](https://www.linkedin.com/in/maxim-astrakhantsev-13a9391b9/).

Your story awaits. Run `/dm` to begin.
