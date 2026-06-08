# Game Master Claude

**A harness that turns Claude Code into a persistent Game Master — running a living game world that's genuinely yours.**

This is not a chatbot you roleplay with. It's a *harness*: a thin, opinionated shell around Claude Code that gives the most capable model on the planet the three things it normally lacks to run a real campaign — **durable memory, a custom rulebook, and a world that keeps moving when you look away.** Claude builds the world, then runs it for you, session after session, remembering everything.

The idea is simple and, as far as we can tell, fairly new: stop asking the model to *pretend* to be a GM inside a single conversation, and instead give it a real GM's tools — state on disk, mechanics it can look up, a clock that ticks. Then get out of its way. Claude does the imagining; the harness makes it stick.

### Two front doors

There are two ways into a world, and both get the same living-world treatment:

- **🌍 Author something original — `/new-game`.** A genre-aware questionnaire interviews you, then Claude authors a *book's worth* of brand-new canon and a custom ruleset — and runs it through an anti-generic pipeline whose explicit job is to keep your world from collapsing into off-the-shelf high fantasy. This is the headline act. ([jump ↓](#-author-an-original-world--new-game))
- **📖 Import a book you own — `/import`.** Drop in a PDF and Claude reads the real text, writes a bespoke game out of *that book*, and drops you into it as whoever you want to be. ([jump ↓](#-import-a-book--import))

Pick either. The persistence, the custom rulebook, the living world, the dying-and-handoff stakes — all identical underneath.

---

## The harness in one picture

```
        YOU                    THE HARNESS                      CLAUDE (Opus)
   "I attack the    →   routes the beat, loads only    →   decides, narrates,
    Terror Clown"       the rules it needs, hands           voices the NPC,
                        Claude the scene + memory           rolls the dice
                                    ↑                              ↓
                        reads & writes campaign state   ←   "persist before you
                        (HP, NPCs, threads, clocks,         narrate" — every
                        consequences) on disk               change saved first
```

Every turn runs the same loop: **gather context → decide → execute → persist state → narrate.** The harness enforces the boring, critical part — *nothing happened until it's written to disk* — so the story survives across days, machines, and context windows. Claude handles the part it's extraordinary at: making it feel alive.

---

## What the harness actually gives the model

- **A memory that outlives the conversation.** NPCs, locations, plot threads, facts, your character sheet, your whole history — all persisted as plain JSON per campaign. Claude can recall prior events, keeps a tiered memoir of the campaign, and tracks what's canon-from-the-book versus what *you* made happen. Close the laptop mid-fight; pick it up next week exactly where you left off.

- **A rulebook written for *your* world, not D&D.** Whether you import a book or author one from scratch, Claude produces a **World Bible** (voice, tone, factions, geography, timeline) and from it a **World Kit** — a custom ruleset with its own stats, its own way of leveling, its own signature systems. A *Dune* import plays like *Dune*; a *Dungeon Crawler Carl* import plays like *Dungeon Crawler Carl*; and an original world plays like *itself*. D&D 5e is just one possible kit, not the foundation.

- **A world that pushes context *to* the model.** The old failure mode of LLM roleplay is amnesia — the GM remembers your HP but forgot the cliffhanger. Here, every scene arrives pre-loaded: *previously on…*, open threads, key facts, which NPCs are present and how they talk, the clocks ticking in the background, and any consequence about to land. Claude doesn't have to remember to look — the harness puts it on the table.

- **A world that keeps living.** Consequences you set in motion fire on their own when you return to a place or enough time passes. Named threat clocks tick whether you're watching or not. Between sessions, a small, bounded set of off-screen developments advance. The place feels alive because it *is* still running.

- **Specialist sub-agents on tap.** A fight starts and a monster-manual agent grabs stats; you cast something and a spell-caster looks up the mechanics; you go shopping and a gear-master handles inventory; a haunting vista appears and a scene-illustrator paints it in the background. They're **book-first** — they read your world's own rules before reaching for anything external — and they spin up invisibly so the story never stops.

- **Real stakes.** The character can die. Telegraphed, earned, never by GM fiat — but death is a valid forward outcome, and when it lands the harness runs a hand-off so the show goes on (take over a party member, roll a newcomer, step in as a canon figure). The world remembers the fallen.

- **An illustrated campaign, drawn in-world.** *If* you drop an `OPENAI_API_KEY` into `.env`, the GM is encouraged to illustrate big beats — a new location, a boss reveal, a haunting vista, your styled flourish — with real generated images, presented diegetically as the work of an **in-world chronicler**: a named artist with a locked art style and persona, both designed at world-creation time to fit your plot and tone. The same hand "draws" every image across the campaign, so your gallery reads like one artist's sketchbook of your story. No key, no problem — the GM just keeps narrating in text and never mentions images.

---

## In Action — Dungeon Crawler Carl

A campaign imported from *Dungeon Crawler Carl*. Tandy the sasquatch rips the skin off a Terror Clown, forces Carl to wear it as a disguise, then performs a sasquatch mating dance to distract Grimaldi while Donut frees the dragon. Standard Tuesday. (Images generated in-world, on the fly, by the scene-illustrator agent.)

![Tandy acquires Terror Clown skin disguise for Carl](public/622422010_1572097020675669_3114747955156903860_n.png)

![Tandy performs a sasquatch mating dance to distract Grimaldi](public/625560066_33916991331281718_1129121114640091251_n.png)

![Exploring The Laughing Crypt — thirty clown bodies wake up](public/623940676_2000130920531570_2521032782764513297_n.png)

---

## 🌍 Author an original world — `/new-game`

Anyone can ask an LLM for "a fantasy setting" and get the same tired tavern, the same chosen one, the same five elemental kingdoms. The interesting problem isn't *generating* a world — it's generating one that doesn't drift to generic. That's what this pipeline is built to defeat.

You don't write the world. You answer a short **genre-aware questionnaire** (powered by interactive multiple-choice prompts), and Claude builds outward from your answers:

- **A one-line premise** in your own words — *"Conan but on a drowned coast,"* *"cozy folk-horror in a town that forgets its dead,"* *"corporate clans fighting over charged ruins."*
- **The genre bend** — the single most important anti-generic lever. Sword-and-sorcery (magic is blood-priced and villainous), high fantasy (deep lineage and old songs), sci-fantasy (nanomagic and clan politics), folk/cosmic horror (a wrongness beneath a fragile community) — each bend pushes the whole world somewhere specific.
- **A narrative voice** — *whose* voice should narrate this world? Howard, Le Guin, Gibson, Pratchett, or your own pick. Claude writes original prose *in that author's fingerprint*, and narrates every beat in it. Your world doesn't read like a generic narrator; it reads like a book.
- **A locked art style** — a deliberately surprising mashup (*"a gilded medieval illuminated manuscript depicting cyberpunk megacities"*) and an in-world chronicler who "draws" every image, so the whole gallery reads like one artist's sketchbook.

From those answers Claude runs a **five-stage authoring pipeline** — *seed → skeleton → fan-out → reconcile → ground*:

1. **Seed.** Your answers become a structured world-seed, with an **adaptive axis list** — Claude picks the dimensions that actually matter for *your* genre (a sword-and-sorcery world gets deep blood-magic lore and skips heavy tech; a sci-fantasy world gets deep infrastructure and corporate factions).
2. **Skeleton.** Claude authors the world's coherent spine in one pass while the seed is fresh — name, voice, themes, factions, geography, signature systems — then **shows it to you for approval before going further.**
3. **Fan-out.** A swarm of specialist `world-author` agents runs *in parallel*, each deepening exactly one axis (geography, factions, history, magic-lore, culture, bestiary…), while a `world-kit-author` derives the custom ruleset from the world — never defaulting to 5e.
4. **Reconcile — the anti-drift pass.** A `world-reconciler` agent reads everything and runs three checks: a **genericness critic** that flags anything that could've come from any generic fantasy, a kit↔flavor agreement check, and a cross-link pass that weaves the axes together. Generic flags get rewritten. *This stage exists for the sole purpose of making your world play distinct, not just read distinct.*
5. **Ground.** All the authored canon is folded into runtime state, compiled, and embedded for retrieval — the **same grounding machinery an imported book gets** — so scenes draw on your world's own canon as if it were a published source.

The result is a world with its own voice, its own rules, its own art, and a corpus deep enough to play in for a hundred sessions. Then Claude hands you to `/create-character` and the story begins.

```
You: /new-game
GM:  A few questions first. One line — what's the world?
You: Wandering swordsmen in a desert of glass where the gods drowned.
GM:  Genre bend? (1) sword-and-sorcery  (2) high fantasy  (3) sci-fantasy  (4) folk/cosmic horror
...
```

## 📖 Import a book — `/import`

Got a favorite novel, a classic adventure module, a weird pulp paperback from the 70s? Drop the PDF into `source-material/`, and Claude reads large spans of the actual text, writes a **World Bible** for it, drafts a **World Kit** ruleset, indexes the book for retrieval, and drops you in. Not a reskin — the imported world plays by its *own* logic, and narration stays grounded in real passages until your choices change things.

> **Where to find books:** the [Internet Archive](https://archive.org/) is a goldmine — thousands of free books, modules, and old pulp novels. Jump into *IT* and help the bad guys. Drop into *Lord of the Rings* and play from Gollum's perspective. It's your call.

---

## Getting Started

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

```bash
git clone https://github.com/Sstobo/Claude-Code-Game-Master.git
cd Claude-Code-Game-Master
./install.sh
```

The install script sets up everything — Python, uv, jq, and all dependencies. It works on macOS and Linux with zero prior setup. (You can also just launch Claude Code and ask it to set things up.)

Then launch and play:

1. Run `claude` to launch Claude Code
2. Run `/gm` — the harness takes it from there

`/gm` is the only command you need. It offers a **New Adventure** — author an original world (`/new-game`), import a book you've dropped in `source-material/` (`/import`), or spin up a quick one-shot — then builds your character and runs the game. First thing it asks once a world exists: **"Who are you in this world?"** — play a character lifted straight from the source, an original of your own, or a nameless traveler who wanders in. The mechanics get figured out behind the scenes.

---

## Why a harness, and not just a long prompt

A single mega-prompt can fake a GM for one session. It can't remember your campaign next week, it can't enforce its own rules, and it drowns the model in mechanics it doesn't need this turn. The harness solves each of those directly:

- **Thin always-on core, heavy rules on demand.** A lean router stays in context; combat, social, skill checks, conditions, leveling, dungeon crawls, and narration craft load *only* for the moment that needs them. The model spends its attention on the scene, not the manual.
- **State on disk, not in the context window.** Memory is bounded by your filesystem, not the token limit. Campaigns can run indefinitely.
- **Persist-before-narrate, enforced.** Every state change is written before a word reaches you, so a crash or a context reset never loses your progress.
- **Grounded in a real corpus.** Scenes draw on actual passages — your imported book, or the canon Claude authored for your original world — via a local retrieval index, so narration stays true to the source until your choices change it.

You never see any of this. You just see the story.

---

## Advanced

Everything below is handled automatically by `/gm`. These are here if you want manual control.

### One Command

There's really just one command you ever need:

| Command | What it does |
|---------|--------------|
| `/gm` | **Everything.** Start or continue your story. The harness imports a book, builds a world, creates your character, runs a one-shot, saves, and shows your sheet — just talk to it. |

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
| `scene-illustrator` | High-impact visual beats |
| `create-character` | New characters |

### Bash Tools

The harness is plumbing you can poke at: bash wrappers (`tools/`) → Python managers (`lib/`) → per-campaign JSON (`world-state/campaigns/<name>/`). All tools follow the pattern `bash tools/gm-<tool>.sh <command> [args]`. Most accept `--json` for structured output.

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

### The D&D 5e API, when it fits

If your world *is* D&D-flavored, the harness can pull official rules, monsters, spells, and gear from the [D&D 5e API](https://www.dnd5eapi.co/) — grounding numbers in real mechanics instead of guessing. For every other book, your World Kit runs the show.

### Dependencies

Installed automatically during setup via [uv](https://docs.astral.sh/uv/):

**Core:** `anthropic` (Claude API client), `pdfplumber` + `pypdf2` (PDF extraction), `python-docx` (Word docs), `python-dotenv` (env loading), `requests` (D&D 5e API).

**RAG (document import):** `sentence-transformers` (embeddings), `chromadb` (vector index for source lookups).

---

## License

Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — free to share and adapt for non-commercial use. See [LICENSE](LICENSE) for details.

---

Built by [Sean Stobo](https://www.linkedin.com/in/sean-stobo/). Your story awaits. Run `/gm` to begin.
