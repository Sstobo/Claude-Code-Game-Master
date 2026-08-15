# /import — Step into a book

The book **is** the adventure. Index it. Ask who they came to be. Open that page.
Do not scrape Hyboria into a wiki first.

The dream: a holodeck door and a 1983 D&D table. Someone they love is already in
the room. The rest of the book stays on the GM's chair until play walks toward it.

See `docs/conventions/the-dream.md`.

## Usage

```
/import <file-path> [campaign-name]
```

**Arguments:**
- `file-path` — PDF, DOCX, TXT, or MD
- `campaign-name` — optional (defaults to a sane name, never the OceanofPDF filename)

---

## Step 1: Get the file

If arguments weren't provided, check `source-material/`:

```bash
ls -la source-material/ 2>/dev/null | grep -E '\.(pdf|docx|txt|md)$'
```

List what you found, or ask them to drop a file / paste a path. Then ask for a
campaign name (or pick a short one from the title — `conan`, not the dump filename).

---

## Step 2: Put the book on the shelf

This is the only expensive, once-per-book step. Local embeddings. No LLM census.

```
Reading the book and putting it on the shelf...
```

```bash
bash tools/gm-extract.sh prepare "<file-path>" "<campaign-name>"

# REQUIRED here — every RAG read resolves against the ACTIVE campaign.
bash tools/gm-campaign.sh switch "<campaign-name>"

EXPECTED=$(uv run python lib/campaign_manager.py slugify "<campaign-name>")
ACTIVE=$(bash tools/gm-campaign.sh active)
ACTIVE_SLUG=$(uv run python lib/campaign_manager.py slugify "$ACTIVE")
if [ "$ACTIVE_SLUG" != "$EXPECTED" ]; then
    echo "MISMATCH — active is '$ACTIVE', expected '$EXPECTED'" >&2
    exit 1
fi
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
```

**If this block exits non-zero, STOP.** Do not draft a bible. Do not build a stage.

The book is now searchable. That is enough of a "world" to start.

---

## Step 3: The door, not the gazetteer

Do **not** launch extractor agents. Do **not** preview entity counts. Do **not**
ask "what should I extract?"

Ask, in the book's tone:

**Who are you in this world — or who did you come to meet?**

Three doors (same as `/gm` identity-first):

- someone from the book (name a few you can actually find via RAG — Conan, Bêlit, Valeria…)
- someone of their own
- no one yet

They came for the fantasy of talking to a favorite character. Spend the spike on
that, not on ability scores and not on a loading screen.

Then, before you build the stage, ask **one more** question — where/when they want
to begin:

**Where — or when — do you want to start?** Offer a fitting default (an iconic
opening scene for this book/character) but make it plain they can name their own:
a specific location, a particular moment or scene from the source, or a point in
the character's timeline ("the night Bêlit dies," "before he was king," "the sack
of such-and-such city"). Persist their answer into the play pack's `room`/`hook`
and build Step 5's stage around **that** start, not the book's default first page.

---

## Step 4: World identity (tone, not inventory)

Draft the bible, kit, voice, and chronicler so the holodeck *sounds* like the book.
This is identity. It is not a census.

```bash
bash tools/gm-extract.sh draft-bible --name "<World/Book Name>"
```

Read large spans of `current-document.txt` (the chapters that carry the world's
voice). Merge authorship:

```bash
bash tools/gm-extract.sh draft-bible --fields-json '{
  "tone": "...",
  "themes": ["..."],
  "factions": {"nodes": [{"id":"thieves","name":"Thieves of the Maul"},{"id":"yara","name":"Priesthood of Yara"}], "edges": [{"from":"yara","to":"thieves","relation":"preys on / is feared by"}]},
  "geography": {"nodes": [{"id":"maul","name":"The Maul"},{"id":"tower","name":"Elephant Tower"}], "edges": [{"from":"maul","to":"tower","adjacency":"across the temple quarter"}]},
  "signature_systems": ["..."]
}'
uv run python lib/world_bible.py validate
```

Keep factions/geography as a **handful of horizon names**, not a gazetteer — but
**wire 2–4 edges** (a tension between two factions, an adjacency between two
places). Nodes with no edges are a cast list, not a world; a couple of real
relationships (the villain's faction vs the player's, the caravan vs the hunt)
pay off in every scene. Do not build a full relationship map.

Kit — `dnd5e` only when the file is a D&D module. Everything else is `custom`.
D&D-lean resolution (d20, six abilities) is fine as the table's foundation.

```bash
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
[ -f "$CAMPAIGN_DIR/ruleset.json" ] || bash tools/gm-extract.sh draft-ruleset \
  --attributes "str,dex,con,int,wis,cha" \
  --progression-model "milestone" \
  --kit "custom"
```

```bash
bash tools/gm-extract.sh campaign-rules
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
uv run python lib/overview_seed.py "$CAMPAIGN_DIR" \
  --fields-json '{"campaign_name":"<World>","genre":"...","tone":{"grim":40,"adventure":40,"horror":20}}' \
  --fix-rules-doc
```

Write a short `rules.md` if the book has signature systems, then point the kit at it.

**Make the signature systems executable — dice, not vibes.** Instantiate 1–3 of
the `game_core` primitives, name them for this world, and persist onto the kit so
the GM *rolls* them:

```bash
bash tools/gm-extract.sh write-systems --systems-json '[
  {"primitive":"named_track","name":"Menace","config":{"max":6,"thresholds":[{"at":3,"consequence":"men step aside for you"},{"at":6,"consequence":"the city turns out to hunt you"}]}},
  {"primitive":"price_roll","name":"Sorcery'"'"'s Price","config":{"dice":"1d20","ladder":[{"min_roll":15,"cost":"a night lost to dreams"},{"min_roll":5,"cost":"a year of your life"},{"min_roll":-99,"cost":"something now watches you"}]}}
]'
```

Primitives: **named_track** (a Menace/Dread/Corruption meter with threshold beats),
**price_roll** (forbidden power exacts a cost), **reaction_roll** (reputation shifts
an NPC's opening stance), **guarded_payoff** (treasure guarded/cursed — roll before
the hand closes). They ride into every scene as YOUR WORLD'S SIGNATURE SYSTEMS.

Voice — verbatim excerpts only (the filter drops paraphrase):

```bash
bash tools/gm-extract.sh draft-bible --voice-json '{
  "style": "...",
  "sample_passages": ["<verbatim 1>", "<verbatim 2>"],
  "vocab": ["..."]
}'
uv run python lib/world_bible.py validate
uv run python lib/world_bible.py review
```

Ask them: **looks right — play it** / **change something**.
`uv run python lib/world_bible.py confirm` only after they say so.

Chronicler (once):

```bash
bash tools/gm-image.sh chronicler \
  --name "<in-world artist>" \
  --style "In the style of ..." \
  --persona "..."
```

---

## Step 5: Build the STAGE — only this room

After they pick a door, read the book for **that** opening. Persist nothing else.

A stage is:

- **1 location** you can stand in (a room, a deck, an alley — not a kingdom)
- **2–4 exits** you can see from here (names + connections; do not fully build the destinations)
- **2–4 people** in this room
- **0–2 objects** in hand or in reach
- **1 hook** that will not wait until morning

```bash
bash tools/gm-search.sh --rag-only "<character or opening scene>" 8
bash tools/gm-lore.sh "<place>" --important
```

Then persist the pack and the stage, before narrating:

```bash
bash tools/gm-playpack.sh set --json '{
  "whose_story": "<who they came to meet or be>",
  "room": "<this room, not a kingdom>",
  "present": ["<2-4 names in the room>"],
  "exits": ["<what you can see from here>"],
  "hook": "<the problem that will not wait>",
  "offstage": ["<horizon names — do not build>"],
  "primer": "<one short GM paragraph>"
}'
bash tools/gm-playpack.sh stage
```

**Give the story a spine — seed the antagonist's clock.** A stage without a
countdown is inert. Seed **at least one** threat clock whose aim completes
off-screen whether or not the player engages — the book's looming danger (Yara's
sorcery, the caravan fleeing the city, the cult's ritual):

```bash
bash tools/gm-clock.sh add "<the antagonist's aim>" 4 --on time \
  --consequence "<what happens in the world when it fills>"
```

One clock, grounded in the book's plot — not a gazetteer of doom. It rides into
every scene as a THREAT CLOCK and ticks on `gm-time.sh`.

When play walks toward a new name: `bash tools/gm-playpack.sh from-book "<name>"` then RAG.

Onboard the PC (the play pack's room + hook are the opening; onboard keeps them):

```bash
bash tools/gm-player.sh onboard canon "<NPC name>"
# or: onboard original "<name>" "<one-line concept>"
# or: onboard nameless
```

If they want a full sheet, `/create-character` is opt-in — never the price of entry.

Enhance **only** the people in this room (so they speak in the book's words):

```bash
bash tools/gm-enhance.sh query "<Name>"
bash tools/gm-enhance.sh apply "<Name>"
```

Do **not** run `gm-enhance.sh batch`. Do **not** run the four extractors **as a
census** (full records + `cap` / `reconcile` / `stub-npcs` / `integrity`). The
one sanctioned extractor use is the light World Index below — pointers, not a
gazetteer. An unresolved name means not on stage yet.

---

## Step 5.5: Build the World Index (a light roster — NOT a census)

The index is a scannable menu of the named things that actually exist in this
book — **one sentence each** — so the GM reaches for real names (Yara, the
Elephant Tower, Yag-kosha) instead of inventing generic ones. It is NOT the
census: no full records, no stats, no `cap`/`reconcile`/`stub-npcs`/`integrity`.

Spawn the extractor agents over the campaign's chunks — **hard cap 6 agents, and
state that 6-agent cap INSIDE each subagent prompt** (subagents self-fan-out).
Ask each for **named entities only** (drop nameless walk-ons), each reduced to
`{name, note}` where the note is ONE sentence:

- `extractor-npcs` → `index.npcs`
- `extractor-locations` → `index.locations`
- `extractor-items` → `index.items`
- `extractor-monsters` (or the monster pass) → `index.monsters`

Dedup by name, then persist in a single call:

```bash
bash tools/gm-extract.sh write-index --index-json '{"npcs":[{"name":"Yara","note":"The dread priest of the Elephant Tower."}],"locations":[...],"items":[...],"monsters":[...]}'
```

The index rides into scene context every session (the WORLD INDEX block). You
still build **no** full records here — a face becomes real only when play walks
toward it (`gm-playpack.sh from-book`, then RAG).

---

## Step 6: Open the door

Narrate the room. Let them talk. One beat. The book is right there — `gm-context.sh`
and `gm-search.sh --rag-only` when someone new walks on. Persist that one new face
or place, then keep playing.

The campaign JSON is a journal of where you've been. Grow it from the table.

---

## Leftover machinery (do not use on a new import)

`gm-extract.sh` still has `normalize`, `cap`, `reconcile`, `stub-npcs`, `integrity`,
and the four extractor agents. Using them to build **full records** is the old
**census** path — it front-loads a gazetteer so a graph looks complete. That is
the opposite of this command. Leave the census machinery. (The extractor agents
have exactly one sanctioned use here: the light one-sentence World Index in
Step 5.5 — pointers, never records.) If an operator is repairing a legacy import,
see `docs/import-guide.md`.

---

## Done

```
The book is on the shelf. The door is open.
```

Hand off to `/gm`. Do not present a second menu. Identity already happened.
