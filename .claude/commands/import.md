# /import - Import Your Adventure

Import a D&D book, adventure module, or any document and extract it into a playable campaign.

## Usage

```
/import <file-path> [campaign-name]
```

**Arguments:**
- `file-path` - Path to PDF, DOCX, TXT, or MD file
- `campaign-name` - Optional name (defaults to filename)

---

## Step 1: Get File Information

If arguments weren't provided, first check the source-material folder:

```bash
ls -la source-material/ 2>/dev/null | grep -E '\.(pdf|docx|txt|md)$'
```

**If files are found**, display them as options:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  IMPORT YOUR ADVENTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found documents in source-material/:

  1) [filename.pdf]
  2) [filename2.docx]
  ...

  Or: Drag/drop a different file, or paste a path

Supported formats: PDF, DOCX, TXT, MD
```

Use AskUserQuestion to let them pick from the list OR provide their own path.

**If no files in source-material/**, display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  IMPORT YOUR ADVENTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Drag and drop your file here, or paste the file path.
(Tip: You can also place files in source-material/)

Supported formats: PDF, DOCX, TXT, MD
```

Then ask for campaign name (or use filename as default).

---

## Step 2: Vectorize the Document

Show progress as the document is prepared:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PREPARING: "<filename>"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reading your adventure and preparing it for play...
```

Run the prepare command, then make the new campaign ACTIVE immediately:
```bash
bash tools/gm-extract.sh prepare "<file-path>" "<campaign-name>"

# REQUIRED, and it must happen here — not at the end. Every RAG read from now on
# (the Step 3 preview, and every `gm-search.sh --rag-only` the four extractor
# agents run) resolves against the ACTIVE campaign's vector store. Switch late and
# the agents query the previous campaign's book, or no book at all.
bash tools/gm-campaign.sh switch "<campaign-name>"

# ASSERT the switch took. A failed switch is silent-but-poisonous: the preview and
# all four extractors would read the PREVIOUS campaign's book and write plausible
# entities from the wrong source.
EXPECTED=$(uv run python lib/campaign_manager.py slugify "<campaign-name>")
ACTIVE=$(bash tools/gm-campaign.sh active)
# Compare slugs, not raw strings: a legacy-named folder resolves to its own
# directory name, which is still the right campaign.
ACTIVE_SLUG=$(uv run python lib/campaign_manager.py slugify "$ACTIVE")
if [ "$ACTIVE_SLUG" != "$EXPECTED" ]; then
    echo "MISMATCH — active is '$ACTIVE', expected '$EXPECTED'" >&2
    exit 1
fi
echo "Active campaign: $ACTIVE"

# From here on, ALWAYS resolve the campaign directory through the tool. Never
# hand-build "world-state/campaigns/<campaign-name>" from the display name —
# that is the unslugged path, and it is a different directory.
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
echo "Campaign directory: $CAMPAIGN_DIR"
```

**If this block exits non-zero, STOP.** Do not run the preview and do not
launch the extractors. Report the mismatch to the user and fix it (usually the
campaign name given to `prepare` differs from the one passed to `switch`) before
continuing.

After completion, display what was processed:
```
  ├─ Extracting text............... done
  ├─ Splitting into sections....... done
  ├─ Building search index......... done
  └─ Ready for extraction!
```

---

## Step 3: Preview What's In The Book

Run sample queries to show the user what content is available:

```bash
# Sample queries to detect content types
bash tools/gm-search.sh --rag-only "character name person NPC" 5
bash tools/gm-search.sh --rag-only "location place room dungeon" 5
bash tools/gm-search.sh --rag-only "item treasure weapon magic" 5
bash tools/gm-search.sh --rag-only "quest mission objective plot" 5
```

Display a preview:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DOCUMENT READY!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I've scanned your adventure. Here's what I found:

  Characters mentioned:  ~[count] names detected
    ([sample names from query results]...)

  Locations described:   ~[count] places
    ([sample locations from query results]...)

  Items & Treasures:     ~[count] references
    ([sample items from query results]...)

  Quests & Hooks:        ~[count] storylines
    ([sample plot elements from query results]...)
```

---

## Step 4: Offer Extraction Options

Ask the user what to extract:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WHAT SHOULD I EXTRACT?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I can pull out detailed information for:

  [x] NPCs - Characters with descriptions & personalities
  [x] Locations - Places with connections & features
  [x] Items - Treasures, magic items, equipment
  [x] Quests - Story hooks, objectives, rewards

  1) Extract all (recommended)
  2) Let me choose which ones
  3) Skip extraction - I'll reference the book myself
```

Use AskUserQuestion with options:
- "Extract all (Recommended)" - Extract NPCs, locations, items, and quests
- "Let me choose" - Show checkboxes for each type
- "Skip extraction" - Just use the search index, no structured extraction

---

## Step 5: Run Extraction Agents

Display extraction progress:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EXTRACTING CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Four agents are reading your adventure...

  NPCs ............ [working]
  Locations ....... [working]
  Items ........... [working]
  Quests .......... [working]

Agents work in parallel - this may take a few minutes.
```

**CRITICAL**: Launch all 4 agents simultaneously using parallel Task tool calls.
Resolve the directory FIRST and paste that literal path into every prompt — never
interpolate the display name under `world-state/campaigns/`:

```bash
bash tools/gm-campaign.sh path    # -> <campaign-dir>, use this exact string below
```

```
Task: subagent_type=extractor-npcs
prompt: "Extract characters from: <campaign-dir>/chunks/
         Find every character/NPC/person via RAG queries (the campaign is active).
         Write output to: <campaign-dir>/extracted/npcs.json"

Task: subagent_type=extractor-locations
prompt: "Extract places from: <campaign-dir>/chunks/
         Find every location/setting/scene via RAG queries (the campaign is active).
         Write output to: <campaign-dir>/extracted/locations.json"

Task: subagent_type=extractor-items
prompt: "Extract objects from: <campaign-dir>/chunks/
         Find every item/object/prop via RAG queries (the campaign is active).
         Write output to: <campaign-dir>/extracted/items.json"

Task: subagent_type=extractor-plots
prompt: "Extract story elements from: <campaign-dir>/chunks/
         Find every quest/scene/theme/plot point via RAG queries (the campaign is active).
         Write output to: <campaign-dir>/extracted/plots.json"
```

As each agent completes, update the display:
```
  NPCs ............ done! (23 found)
  Locations ....... done! (15 found)
  Items ........... done! (42 found)
  Quests .......... done! (8 found)
```

---

## Step 5.5: Validate Extraction Results

**CRITICAL**: After ALL agents report completion, validate their output before proceeding.

```bash
bash tools/gm-extract.sh validate "<campaign-name>"
```

This is a **gate, not a report**. It checks that all 4 extraction files exist, contain
valid JSON, and hold entities — counting list-shaped and dict-shaped agent output alike.
It exits non-zero when a file is missing, is unparseable, or `npcs`/`locations` came back
empty, naming the failing type and the reason. Empty `items`/`plots` only warn: a book with
no treasure or no explicit quest hooks is unusual, not broken.

**If validation passes** (exit 0):
- Continue to Step 6

**If validation fails** (non-zero exit):

**STOP. Do not run any command from Step 6.** `normalize`, `cap`, `reconcile`, and the
integrity gate all read this output; running them on missing or empty extraction writes a
half-empty campaign that looks imported. Wait for the user's answer below before continuing.

Display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  EXTRACTION INCOMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Some extraction agents failed or returned empty results.

  [validation output showing which files failed]

What would you like to do?
```

Use AskUserQuestion with these options:
- **"Retry failed extractions"** - Re-launch agents only for the types the gate named, then validate again
- **"Cancel import"** - Stop the import process

There is deliberately **no "continue with partial data"** option. The gate only fails on
output the rest of the pipeline cannot work from — a missing or unparseable file, a
malformed entity, or a book that yielded no cast or no places — and every Step 6 pass reads
that output. Continuing would write a half-empty campaign that looks imported. A thin but
valid extraction (no items, no plot hooks) already passes with a warning and needs no
override.

**Do NOT proceed silently with missing data.** The whole point of import is to extract content from the source material. If extraction failed, the user must be informed and given options.

---

## Step 6: Normalize Extracted Files to Campaign Root, then Archive

After all agents complete:

```bash
set -e   # the gate below is mechanical: a failed pass stops the chain here

# Re-assert the Step 5.5 gate. Under `set -e` a non-zero validate ends the block
# before normalize touches the campaign root.
bash tools/gm-extract.sh validate "<campaign-name>"

# Normalize extracted/*.json into the campaign root in the flat {name: {...}}
# shape the runtime managers require. Extractor agents emit a bare list (what
# extraction_schemas.py declares), a keyed dict, or either nested under a wrapper
# key beside document/metadata scraps; a plain `cp` would leave a list the runtime
# cannot key, or one giant entity named "npcs". NEVER `cp` these files.
bash tools/gm-extract.sh normalize "<campaign-name>"

# Cap each type to the top-30 most important entities (mention-frequency +
# plot-reference/party boost). We do NOT need every walk-on NPC or one-off
# platform — just the playable core. Runs before enhancement so dropped
# entities aren't enhanced. Reports dropped counts to the user.
bash tools/gm-extract.sh cap "<campaign-name>" 30

# Item correctness: clear lore-only `cursed` flags (keep only mechanical penalties),
# reclassify overloaded `wondrous` into key/portal/lootbox/coupon, null non-price values.
bash tools/gm-extract.sh fix-items "<campaign-name>"

# Normalize connection targets: canonicalize drifted `connections.to` to real keys
# and move routing rule-phrases ("Any line", "Transfer stations ending in 1") into
# notes so reconcile doesn't drop them. Runs BEFORE reconcile.
bash tools/gm-extract.sh normalize-connections "<campaign-name>"

# Reconcile missing locations: stub (with a source passage + bidirectional hub
# link) or drop every location reference that doesn't resolve to a node. Runs
# BEFORE the integrity gate so location refs resolve.
bash tools/gm-extract.sh reconcile "<campaign-name>"

# Stub missing NPC refs: the hard cap can drop NPCs that plots still reference;
# create a minimal stub for each so plot.npcs resolves, and normalize plot types.
# Runs BEFORE the integrity gate.
bash tools/gm-extract.sh stub-npcs "<campaign-name>"

# Stat combat NPCs: assign a coarse difficulty-proxy (hp + cr/difficulty) so every
# combatant is runnable out of the box, and flag non-combatants statless. Exact stat
# blocks still come from the monster-manual agent at encounter time.
bash tools/gm-extract.sh stat-npcs "<campaign-name>"

# Integrity gate: canonicalize every cross-reference (plot.npcs, plot.locations,
# npc.location_tags, location.connections) to a real entity key via the alias
# resolver, recording variants as `aliases`. Strict by default — FAILS the import
# on any unresolved reference (after reconcile has stubbed/rewritten locations).
bash tools/gm-extract.sh integrity "<campaign-name>"

# Plot spine: order the MAIN plots into the book's arc (sequence + depends_on) and
# record a through-line on the overview, so STORY THREADS read as a narrative arc,
# not a flat bag of hooks.
bash tools/gm-extract.sh spine "<campaign-name>"

# Seed threat clocks: detect the book's headline time pressure (e.g. a "collapse
# in N days" countdown) in the plots and create real threat_clocks entries with a
# full-clock consequence + linked plot, so the arc has live pressure (not just prose).
bash tools/gm-extract.sh seed-clocks "<campaign-name>"

# Seed the opening beat: set the starting player_position to the arc's opening
# location, mark the first spine plot active with an opening beat, and write a
# session-log "Previously On / Where We Paused" hook — so the first /gm session
# opens on the book's actual opening, not a blank void. (Run after spine.)
bash tools/gm-extract.sh seed-opening "<campaign-name>"

# Archive the extracted/ folder (temporary working directory)
bash tools/gm-extract.sh archive "<campaign-name>"
```

**Note**: The `extracted/` folder is a temporary working directory. `normalize`
writes the flat `npcs.json` / `locations.json` / `items.json` / `plots.json` to
the campaign root; archive `extracted/` afterward to keep the folder clean.

---

## Step 6.5: Establish the World Kit (ruleset.json) — REQUIRED

Every campaign's rules come from its **World Kit** (`ruleset.json`). If you skip
this, `WorldKit` silently falls back to `DEFAULT_RULESET` ("Generic Adventure"
with an EMPTY attribute list and the wrong name) — the imported book will play on
hollow, mismatched rules. Do not skip.

```bash
# Resolved, never hand-built: the campaign has been active since Step 2, and
# "world-state/campaigns/<campaign-name>" would be the UNSLUGGED path — a second,
# empty directory that the runtime (which reads the slugged one) never sees.
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
[ -f "$CAMPAIGN_DIR/ruleset.json" ] && echo "World Kit already present" || echo "NO World Kit — must create one"
```

If no `ruleset.json` exists, author one **inferred from the source book**:

- **Same universe as an existing campaign?** (e.g. another Dungeon Crawler Carl
  book) Copy that campaign's `ruleset.json` — the kit is universe-level, not
  campaign state: `cp "$(bash tools/gm-campaign.sh path "<sibling>")/ruleset.json" "$CAMPAIGN_DIR/ruleset.json"`
- **Otherwise**, write a kit that fits the book. Baseline template (adjust to the
  source — sci-fi/horror/non-D&D books often need different attributes or a
  `resource-axis` / `milestone` progression rather than levels):

```bash
cat > "$CAMPAIGN_DIR/ruleset.json" <<'JSON'
{
  "name": "<World/Book Name>",
  "stat_schema": { "attributes": ["str","con","dex","int","wis","cha"], "vitals": ["hp"] },
  "progression": { "model": "milestone" },
  "resolution": { "model": "d20-vs-dc" },
  "active_agents": ["monster-manual","rules-master","spell-caster","gear-master","loot-dropper","npc-builder"],
  "rules_doc": null
}
JSON
```

Verify the kit (read the file directly, so the check is pinned to the campaign
being imported rather than to whatever `world_kit.py info` finds active):
```bash
uv run python -c "import json; k=json.load(open('$CAMPAIGN_DIR/ruleset.json')); print('Kit:', k['name'], '| attrs:', k['stat_schema']['attributes'])"
```
Confirm `name` is the book's world (not "Generic Adventure") and the attribute list is non-empty.

---

## Step 6.6: Author the Overview + campaign_rules — REQUIRED

The World Kit (ruleset.json) is a thin router. The book's signature SYSTEMS live in
`campaign-overview.json`'s `campaign_rules` block — `WorldKit.campaign_rules()` reads
them into scene context. A fresh import leaves the overview as the default scaffold
(genre "Fantasy", date "Year 1", no campaign_rules), so without this step the book's
flavor is captured nowhere the GM tooling reads.

Author real overview content from the source and write a `campaign_rules` block
describing the book's signature systems, then resolve any dangling `rules_doc`:

```bash
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)   # re-derive; never hand-build it
uv run python lib/overview_seed.py "$CAMPAIGN_DIR" \
  --fields-json '{"campaign_name":"<World/Book Name>","genre":"<e.g. LitRPG / Comedy-Horror>","tone":{"horror":30,"comedy":35,"drama":35}}' \
  --rules-json '{"<system_key>":"<one-line rule the GM enforces>", "...":"..."}' \
  --fix-rules-doc
```

For a DCC import, `campaign_rules` should cover: viewer-based progression, loot boxes,
saferooms/shops, the moving Iron Tangle trains, prime-station stairwells, and the
collapse clock. `--fix-rules-doc` nulls a `rules.md` pointer with no file on disk.

Then author substantive GM-facing rules prose grounded in the source and point the
kit at it (this is the per-book rules meat the thin ruleset.json routes to):

```bash
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)   # re-derive; never hand-build it
# Write $CAMPAIGN_DIR/rules.md — GM-facing guidance for the book's signature systems
# (progression, loot, saferooms, world mechanics, the headline clock, tone). Then:
uv run python -c "import sys;sys.path.insert(0,'lib');from overview_seed import set_rules_doc;print(set_rules_doc('$CAMPAIGN_DIR','rules.md'))"
```
`WorldKit.rules_doc_path()` loads it on demand. Write real guidance, not raw passages.

Verify (the campaign is already active from Step 2):
`uv run python -c "import sys;sys.path.insert(0,'lib');from world_kit import WorldKit;print(list(WorldKit().campaign_rules().keys()))"`
— the campaign_rules keys must be non-empty.

---

## Step 6.7: Capture the Narrative Voice (world-bible `voice`) — REQUIRED

The GM narrates in the book's voice ONLY if `world-bible.json` carries it —
`get_full_context` surfaces a `NARRATIVE VOICE` block (style + sample passages)
every beat. A bible with an empty `voice` makes play read like a generic narrator,
not like the book. Populate it from the SOURCE:

- `style` — a concrete prose fingerprint of the author (sentence rhythm, diction,
  imagery), inferred from `current-document.txt`.
- `sample_passages` — 2-3 SHORT, **verbatim** excerpts of the author's prose from
  the source (fair-use sized). These are the GM's imitation targets, so they must
  be the real text, not paraphrase.
- `vocab` — a few signature in-world terms.

Use the grounding helper so only verbatim excerpts survive (it drops anything not
found in the source), then merge into the bible and validate:

```bash
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
CAMPAIGN_DIR="$CAMPAIGN_DIR" uv run python - <<'PY'
import os, sys, json; sys.path.insert(0, "lib")
from book_bible import draft_voice
CAMP = os.environ["CAMPAIGN_DIR"]   # resolved by the tool, never hand-built
src = open(f"{CAMP}/current-document.txt", encoding="utf-8").read()
voice = draft_voice(
    style="<author's prose fingerprint>",
    sample_passages=["<verbatim excerpt 1>", "<verbatim excerpt 2>"],
    source_text=src,
    vocab=["<signature term>"],
)
bible = json.load(open(f"{CAMP}/world-bible.json"))
bible["voice"] = voice
json.dump(bible, open(f"{CAMP}/world-bible.json", "w"), indent=2, ensure_ascii=False)
print("voice passages kept:", len(voice["sample_passages"]))
PY
uv run python lib/world_bible.py validate
```

Confirm `voice.style` is set and ≥1 `sample_passages` survived (if zero survived,
your excerpts were not verbatim — re-copy them exactly from the source).

---

## Step 6.8: Lock the Chronicler + Art Style — REQUIRED

The gallery's visual signature is a world-identity decision made HERE, once — not
improvised per-image at play. Derive it from the book's tone and lock it so the
`scene-illustrator` agent opens EVERY prompt with the same style:

```bash
bash tools/gm-image.sh chronicler \
  --name "<in-world artist who 'makes' every image; fits the book>" \
  --style "<MUST start with 'In the style of ...'; a CREATIVE, MULTIFACETED mashup — combine two unexpected references, e.g. 'In the style of Frank Miller's Batman but in smudged charcoal', 'In the style of a Bayeux-tapestry embroidery but depicting a neon megacity'. Aim for the OHHHHH.>" \
  --persona "<their voice/bias — grim, sarcastic, reverent, unreliable>"
```

The agent never picks its own style; it reads this locked one. Make the mashup surprising.

---

## Step 7: Show Summary

The campaign has been active since Step 2. Count and display what was extracted:

```bash
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
uv run python -c "import json; d=json.load(open('$CAMPAIGN_DIR/npcs.json')); print(f'NPCs: {len(d)}')"
uv run python -c "import json; d=json.load(open('$CAMPAIGN_DIR/locations.json')); print(f'Locations: {len(d)}')"
uv run python -c "import json; d=json.load(open('$CAMPAIGN_DIR/items.json')); print(f'Items: {len(d)}')"
uv run python -c "import json; d=json.load(open('$CAMPAIGN_DIR/plots.json')); print(f'Plot Hooks: {len(d)}')"
```

Display the summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YOUR WORLD IS READY!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Campaign: "<campaign-name>"

  [count] NPCs ready to meet
     [sample 3-4 NPC names from the extracted data]...

  [count] Locations to explore
     [sample 3-4 location names]...

  [count] Items & Treasures
     [sample 3-4 item names]...

  [count] Quest Hooks active
     [sample 3-4 quest names]...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 7.5: Batch RAG Enhancement (CRITICAL FOR QUALITY)

**This step primes all extracted entities with source material context.**

Display progress:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ENHANCING ENTITIES WITH SOURCE MATERIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connecting extracted entities to original text passages...
This ensures rich, authentic gameplay context.
```

Run the batch enhancement:
```bash
bash tools/gm-enhance.sh batch
```

This will:
1. Query RAG for each extracted entity (NPCs, locations, items, plots)
2. Store the top matching passages with each entity
3. Enable rich scene descriptions during gameplay

Display completion:
```
  Enhancement complete!
  ├─ [X] entities enhanced with source passages
  └─ Ready for authentic gameplay

Your world now has deep connections to the source material.
NPCs will speak with their original voices, locations will
feel true to the book.
```

**Why this matters:**
- Without enhancement, entities are just names and brief descriptions
- With enhancement, each entity has 3-5 source passages attached
- During gameplay, the GM can draw on this context for authentic narration

---

## Step 8: Transition to Character Creation

Display:

```
The book IS your world - all the NPCs, locations, items, and
quests from your adventure are now ready to play.

Now let's create your character for this adventure!
```

Then automatically run `/create-character` to guide the user through character creation.

---

## Output Location

All content is stored in:

```
world-state/campaigns/<campaign-slug>/    # resolve with: bash tools/gm-campaign.sh path
├── chunks/              # Text chunks from document
├── vectors/             # ChromaDB embeddings for RAG queries
├── extracted/           # Individual agent outputs
│   ├── npcs.json
│   ├── locations.json
│   ├── items.json
│   └── plots.json
├── npcs.json            # Final NPC data (copied from extracted/)
├── locations.json       # Final location data
├── items.json           # Final item data
├── plots.json           # Final quest/plot data
├── campaign-overview.json
├── session-log.md
└── current-document.txt # Full extracted text
```

---

## Content-Type Adaptation

The agents automatically detect and adapt to your content:

| Document Type | Characters | Places | Objects | Story Elements |
|---------------|------------|--------|---------|----------------|
| **D&D Modules** | NPCs, enemies | Rooms, dungeons | Magic items, treasure | Quests, plot hooks |
| **Fiction/Books** | Characters | Settings, scenes | Notable objects | Themes, plot points |
| **Scripts** | Characters | Scenes, locations | Props | Scenes, dialogue |
| **Notes** | People mentioned | Places mentioned | Things mentioned | Ideas, concepts |

---

## Troubleshooting

**No chunks created**: The document may be empty or unreadable. Check `current-document.txt`.

**Agents fail**: Check that chunk files exist in `chunks/` directory.

**Missing content**: Run individual agents again with more specific prompts, or use `bash tools/gm-search.sh --rag-only "search terms"` to search directly.

**Want to enhance extracted entities**: Use `/enhance` to add more detail from source material via RAG.

---

## Done → Play with /gm

Once the campaign is imported, hand the player off to the single front door:

```
================================================================
  ✅ "[Campaign Name]" IS READY TO PLAY
================================================================

  Run /gm to step into the world.
================================================================
```

`/gm` is the canonical entry for every session — do not present a separate
"continue or new" menu here; `/gm` STEP 0 already handles it.
