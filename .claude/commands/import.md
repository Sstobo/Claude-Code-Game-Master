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

Run the prepare command:
```bash
bash tools/dm-extract.sh prepare "<file-path>" "<campaign-name>"
```

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
bash tools/dm-search.sh --rag-only "character name person NPC" 5
bash tools/dm-search.sh --rag-only "location place room dungeon" 5
bash tools/dm-search.sh --rag-only "item treasure weapon magic" 5
bash tools/dm-search.sh --rag-only "quest mission objective plot" 5
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

**CRITICAL**: Launch all 4 agents simultaneously using parallel Task tool calls:

```
Task: subagent_type=extractor-npcs
prompt: "Extract characters from: world-state/campaigns/<campaign-name>/chunks/
         Read all chunk files and extract every character/NPC/person.
         Write output to: world-state/campaigns/<campaign-name>/extracted/npcs.json"

Task: subagent_type=extractor-locations
prompt: "Extract places from: world-state/campaigns/<campaign-name>/chunks/
         Read all chunk files and extract every location/setting/scene.
         Write output to: world-state/campaigns/<campaign-name>/extracted/locations.json"

Task: subagent_type=extractor-items
prompt: "Extract objects from: world-state/campaigns/<campaign-name>/chunks/
         Read all chunk files and extract every item/object/prop.
         Write output to: world-state/campaigns/<campaign-name>/extracted/items.json"

Task: subagent_type=extractor-plots
prompt: "Extract story elements from: world-state/campaigns/<campaign-name>/chunks/
         Read all chunk files and extract every quest/scene/theme/plot point.
         Write output to: world-state/campaigns/<campaign-name>/extracted/plots.json"
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
bash tools/dm-extract.sh validate "<campaign-name>"
```

This checks that all 4 extraction files exist and contain valid JSON.

**If validation passes** (all files present with entities):
- Continue to Step 6

**If validation fails** (missing files, invalid JSON, or all empty):

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
- **"Retry failed extractions"** - Re-launch agents only for missing/empty types
- **"Continue with partial data"** - Proceed with whatever was extracted
- **"Cancel import"** - Stop the import process

**Do NOT proceed silently with missing data.** The whole point of import is to extract content from the source material. If extraction failed, the user must be informed and given options.

---

## Step 6: Normalize Extracted Files to Campaign Root, then Archive

After all agents complete:

```bash
# Normalize extracted/*.json into the campaign root in the flat {name: {...}}
# shape the runtime managers require. Extractor agents inconsistently wrap their
# output (e.g. {"npcs": {...}}, and items.json carries document/metadata keys);
# a plain `cp` would leave those wrappers in place and the runtime would read one
# giant entity named "npcs". `normalize` unwraps them. NEVER `cp` these files.
bash tools/dm-extract.sh normalize "<campaign-name>"

# Cap each type to the top-30 most important entities (mention-frequency +
# plot-reference/party boost). We do NOT need every walk-on NPC or one-off
# platform — just the playable core. Runs before enhancement so dropped
# entities aren't enhanced. Reports dropped counts to the user.
bash tools/dm-extract.sh cap "<campaign-name>" 30

# Reconcile missing locations: stub (with a source passage + bidirectional hub
# link) or drop every location reference that doesn't resolve to a node. Runs
# BEFORE the integrity gate so location refs resolve.
bash tools/dm-extract.sh reconcile "<campaign-name>"

# Integrity gate: canonicalize every cross-reference (plot.npcs, plot.locations,
# npc.location_tags, location.connections) to a real entity key via the alias
# resolver, recording variants as `aliases`. Strict by default — FAILS the import
# on any unresolved reference (after reconcile has stubbed/rewritten locations).
bash tools/dm-extract.sh integrity "<campaign-name>"

# Plot spine: order the MAIN plots into the book's arc (sequence + depends_on) and
# record a through-line on the overview, so STORY THREADS read as a narrative arc,
# not a flat bag of hooks.
bash tools/dm-extract.sh spine "<campaign-name>"

# Seed threat clocks: detect the book's headline time pressure (e.g. a "collapse
# in N days" countdown) in the plots and create real threat_clocks entries with a
# full-clock consequence + linked plot, so the arc has live pressure (not just prose).
bash tools/dm-extract.sh seed-clocks "<campaign-name>"

# Seed the opening beat: set the starting player_position to the arc's opening
# location, mark the first spine plot active with an opening beat, and write a
# session-log "Previously On / Where We Paused" hook — so the first /dm session
# opens on the book's actual opening, not a blank void. (Run after spine.)
bash tools/dm-extract.sh seed-opening "<campaign-name>"

# Archive the extracted/ folder (temporary working directory)
bash tools/dm-extract.sh archive "<campaign-name>"
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
CAMPAIGN_DIR="world-state/campaigns/<campaign-name>"
[ -f "$CAMPAIGN_DIR/ruleset.json" ] && echo "World Kit already present" || echo "NO World Kit — must create one"
```

If no `ruleset.json` exists, author one **inferred from the source book**:

- **Same universe as an existing campaign?** (e.g. another Dungeon Crawler Carl
  book) Copy that campaign's `ruleset.json` — the kit is universe-level, not
  campaign state: `cp world-state/campaigns/<sibling>/ruleset.json "$CAMPAIGN_DIR/ruleset.json"`
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

Verify the kit (read the file directly — `world_kit.py info` reads the *active*
campaign, which isn't switched until Step 7):
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
flavor is captured nowhere the DM tooling reads.

Author real overview content from the source and write a `campaign_rules` block
describing the book's signature systems, then resolve any dangling `rules_doc`:

```bash
uv run python lib/overview_seed.py "$CAMPAIGN_DIR" \
  --fields-json '{"campaign_name":"<World/Book Name>","genre":"<e.g. LitRPG / Comedy-Horror>","tone":{"horror":30,"comedy":35,"drama":35}}' \
  --rules-json '{"<system_key>":"<one-line rule the DM enforces>", "...":"..."}' \
  --fix-rules-doc
```

For a DCC import, `campaign_rules` should cover: viewer-based progression, loot boxes,
saferooms/shops, the moving Iron Tangle trains, prime-station stairwells, and the
collapse clock. `--fix-rules-doc` nulls a `rules.md` pointer with no file on disk.
(The rules-doc-authoring step later writes substantive `rules.md` prose and re-points it.)

Verify: `bash tools/dm-campaign.sh switch "<campaign-name>"` then
`uv run python -c "import sys;sys.path.insert(0,'lib');from world_kit import WorldKit;print(list(WorldKit().campaign_rules().keys()))"`
— the campaign_rules keys must be non-empty.

---

## Step 7: Switch to Campaign and Show Summary

```bash
bash tools/dm-campaign.sh switch "<campaign-name>"
```

Count and display what was extracted:

```bash
CAMPAIGN_DIR=$(bash tools/dm-campaign.sh path)
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
bash tools/dm-enhance.sh batch
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
- During gameplay, the DM can draw on this context for authentic narration

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
world-state/campaigns/<campaign-name>/
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

**Missing content**: Run individual agents again with more specific prompts, or use `bash tools/dm-search.sh --rag-only "search terms"` to search directly.

**Want to enhance extracted entities**: Use `/enhance` to add more detail from source material via RAG.

---

## Done → Play with /dm

Once the campaign is imported, hand the player off to the single front door:

```
================================================================
  ✅ "[Campaign Name]" IS READY TO PLAY
================================================================

  Run /dm to step into the world.
================================================================
```

`/dm` is the canonical entry for every session — do not present a separate
"continue or new" menu here; `/dm` STEP 0 already handles it.
