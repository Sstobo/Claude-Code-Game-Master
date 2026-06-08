# Game Master Claude

**Drop in a book you own. Play *that book* as its own game.**

Got a favorite fantasy novel? A classic adventure module? A weird pulp sci-fi paperback from the 70s? Drop the PDF in, and GM Claude reads it, builds a game out of it, and drops you into that world as whoever you want to be.

Not a reskin. Not D&D-with-the-names-changed. When you import a book, Game Master Claude writes a **bespoke ruleset for that world** — its own stats, its own way of leveling up, its own signature systems (loot boxes, spice visions, train cars, whatever the book runs on). A Dune import plays like Dune. A *Dungeon Crawler Carl* import plays like *Dungeon Crawler Carl*. You don't need to know any of the rules — just say what you want to do.

The [Internet Archive](https://archive.org/) is a goldmine for this. Thousands of free books, modules, and old pulp novels. Jump into *IT* and help the bad guys. Drop into *Lord of the Rings* and play from Gollum's perspective. It's your call.

---

## In Action — Dungeon Crawler Carl

A campaign imported from *Dungeon Crawler Carl*. Tandy the sasquatch rips the skin off a Terror Clown, forces Carl to wear it as a disguise, then performs a sasquatch mating dance to distract Grimaldi while Donut frees the dragon. Standard Tuesday.

![Tandy acquires Terror Clown skin disguise for Carl](public/622422010_1572097020675669_3114747955156903860_n.png)

![Tandy performs a sasquatch mating dance to distract Grimaldi](public/625560066_33916991331281718_1129121114640091251_n.png)

![Exploring The Laughing Crypt — thirty clown bodies wake up](public/623940676_2000130920531570_2521032782764513297_n.png)

---

## Getting Started

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

```bash
git clone https://github.com/Sstobo/Claude-Code-Game-Master.git
cd Claude-Code-Game-Master
./install.sh
```

The install script sets up everything — Python, uv, jq, and all dependencies. It works on macOS and Linux with zero prior setup. (You can also just launch Claude Code and ask it to set things up.)

Then play in three steps:

1. Drop a PDF into the `source-material/` folder
2. Run `claude` to launch Claude Code
3. Run `/gm` — the agent takes it from there

`/gm` handles importing the book, building your character, and running the game. First thing it asks: **"Who are you in this world?"** — play a character lifted straight from the book, an original of your own, or a nameless traveler who wanders in. The mechanics get figured out behind the scenes.

---

## What Makes It Different

### Every book becomes its own game

When you import a document, GM Claude reads large spans of the actual text and writes a **World Bible** for it — voice, tone, factions, geography, timeline, and the systems that make that world tick. From the Bible it drafts a **World Kit**: a custom ruleset for *that* world. It shows you the draft, you confirm it, and you're playing.

The generic core underneath is deliberately thin — a single resolution system (roll vs. a difficulty), abstract health and conditions, and three ways to advance (story milestones, a resource you spend down, or classic XP levels). Everything with flavor — stat names, how combat feels, how you grow stronger — comes from the book. D&D 5e is just *one* possible kit, not the foundation.

### The world pushes the story to you

Old version: the GM had to remember to go look things up. New version: **the world hands the right context to the GM at the right moment.** Every scene arrives pre-loaded with what came before — *previously on…*, the open plot threads, key facts, which NPCs are present and how they talk, the clocks ticking in the background, and any consequences about to land. No more stat-sheet amnesia where the GM knows your HP but forgot the cliffhanger.

### The world keeps living

- **Consequences fire on their own.** Pick a fight, make a promise, leave a body — GM Claude schedules the fallout and it triggers later when you return to a place or enough time passes. With a reason attached, and undoable if the timing's wrong.
- **Threat clocks tick.** Named pressures (a city collapsing in 10 days, a rival closing in) advance whether you're watching or not. When a clock runs out, a beat is due.
- **Between sessions, the world moves.** A small, bounded set of off-screen developments advance while you're away — so the place feels alive when you come back.

### NPCs are people

Every NPC has a goal, a secret, a shifting mood, real relationships with you, and a **canonical voice** pulled verbatim from the book. They sound like themselves, they want things, and they remember how you treated them. Piss off a shopkeeper and it sticks.

### It remembers everything

NPCs, locations, plot threads, facts, your whole history — all of it persists across sessions. GM Claude can recall prior events, keeps a tiered memoir of your campaign, and tracks what's canon-from-the-book versus what *you* made happen. Save and restore at any point.

---

## Under the Hood

You never see any of this — you just see the story — but if you want to pull up the hood:

- **Specialist agents spin up on demand.** A fight starts and the monster-manual agent grabs stats; cast something and the spell-caster looks up the mechanics; go shopping and the gear-master handles the inventory. They're **book-first** — they read your world's own rules before reaching for anything external.
- **Mechanics load only when needed.** A lean always-on core routes to on-demand Skills (combat, social, skill checks, conditions, leveling, dungeon crawls, narration craft) so the heavy rules only load for the moment that needs them.
- **D&D 5e API, when it fits.** If your world *is* D&D-flavored, the system can pull official rules, monsters, spells, and gear from the [D&D 5e API](https://www.dnd5eapi.co/) — grounding numbers in real mechanics instead of guessing. For every other book, your World Kit runs the show.
- **Grounded in the source.** Scenes draw on real passages from your book via a local chapter index, so narration stays true to the text — until your choices change things.

---

## Advanced

Everything below is handled automatically by `/gm`. These are here if you want manual control.

### One Command

There's really just one command you ever need:

| Command | What it does |
|---------|--------------|
| `/gm` | **Everything.** Start or continue your story. From here the GM imports a book, builds a world, creates your character, runs a one-shot, saves, and shows your sheet — just talk to it. |

`/gm` also takes shortcuts if you want them: `/gm save`, `/gm character`, `/gm overview`.

Under the hood, `/gm` calls these for you — you never have to run them yourself, but they exist for manual control:

| Command | What it does |
|---------|--------------|
| `/import` | Import a PDF/document as a new campaign |
| `/new-game` | Build a world from scratch |
| `/create-character` | Build a character in detail |
| `/enhance` | Enrich entities with source-material passages |
| `/world-check` | Validate campaign consistency |
| `/reset` | Clear campaign state |
| `/setup` | Verify/fix installation |
| `/help` | Full command reference |

### On-Demand Skills

The lean core loads these only when the moment calls for it:

| Skill | Loaded when |
|-------|-------------|
| `gm-combat` | A fight breaks out |
| `gm-spellcasting` | You cast something |
| `gm-social` | You talk to / read an NPC |
| `gm-skills` | You attempt something uncertain |
| `gm-dungeon` | You enter a cave, ruin, or complex |
| `gm-conditions` | A status effect is applied |
| `gm-levelup` | You hit a milestone |
| `gm-craft` | Narration and pacing wisdom |

### Specialist Agents

Spawn automatically during play, invisibly:

| Agent | Triggered by |
|-------|--------------|
| `monster-manual` | Combat encounters |
| `spell-caster` | Casting spells |
| `rules-master` | Mechanical edge cases |
| `gear-master` | Shopping, identifying gear |
| `loot-dropper` | Victory, treasure |
| `npc-builder` | Meeting new NPCs |
| `world-builder` | Exploring new areas |
| `dungeon-architect` | Entering dungeons |
| `create-character` | New characters |

### Bash Tools

All tools follow the pattern `bash tools/gm-<tool>.sh <command> [args]`. Most accept `--json` for structured output.

| Tool | Purpose |
|------|---------|
| `gm-campaign.sh` | Create, list, switch, delete campaigns |
| `gm-session.sh` | Session lifecycle, party movement, save/restore |
| `gm-context.sh` | Assemble scene context (world state + source passages) |
| `gm-player.sh` | Player stats — health, progression, gold, inventory |
| `gm-npc.sh` | NPCs — creation, updates, mood/goal/voice, party members |
| `gm-location.sh` | Locations and connections |
| `gm-plot.sh` | Quest and storyline tracking |
| `gm-combat.sh` | Persisted, resumable combat tracking |
| `gm-condition.sh` | Player conditions (poisoned, stunned, etc.) |
| `gm-consequence.sh` | Schedule future events and triggers |
| `gm-recall.sh` | Surface prior events from campaign memory |
| `gm-note.sh` | Record world facts by category |
| `gm-time.sh` | Advance in-game time |
| `gm-search.sh` | Search world state and/or source material |
| `gm-enhance.sh` | RAG-powered entity enrichment |
| `gm-extract.sh` | Document import and extraction pipeline |
| `gm-overview.sh` | Quick world-state summary |
| `gm-image.sh` | Generate a scene image with gpt-image-2 and print a clickable link |
| `gm-reset.sh` | Reset campaign data |

### Scene Images

At high-impact beats — a new location, a boss reveal, a big find — the GM can illustrate the moment with a real image instead of describing it in text:

```bash
bash tools/gm-image.sh generate --title "The Sunken Crypt" \
  --prompt "A flooded stone crypt lit by green torchlight, dark fantasy, cinematic"
```

It calls OpenAI's `gpt-image-2`, saves the PNG into the campaign's `images/` folder, and prints a clickable `file://` link you open to view it (the VS Code terminal linkifies the path). Every generation is logged with an estimated cost — run `gm-image.sh log` for the running total. Requires `OPENAI_API_KEY` in `.env`; without it the GM just keeps narrating in text. Use `--quality low` for quick drafts, `high` for marquee moments.

### Dependencies

Installed automatically during setup via [uv](https://docs.astral.sh/uv/):

**Core:** `anthropic` (Claude API client), `pdfplumber` + `pypdf2` (PDF extraction), `python-docx` (Word docs), `python-dotenv` (env loading), `requests` (D&D 5e API).

**RAG (document import):** `sentence-transformers` (embeddings), `chromadb` (vector index for source lookups).

---

## License

Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — free to share and adapt for non-commercial use. See [LICENSE](LICENSE) for details.

---

Built by [Sean Stobo](https://www.linkedin.com/in/sean-stobo/). Your story awaits. Run `/gm` to begin.
