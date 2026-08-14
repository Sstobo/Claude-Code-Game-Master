# /new-game - Create Your World

Author an original world that plays as *its own game* — grounded by the same
spine an imported book gets: a `world-bible.json`, a `ruleset.json` World Kit, and
an embedded source corpus. The pipeline is **seed → skeleton → fan-out →
reconcile → ground**, so the world does not drift to generic D&D.

> Architecture: original creation *authors* a book's worth of canon, then runs it
> through the SAME grounding machinery import uses. Specialist authors run in
> parallel; each writes ONLY its own files; a serial consolidate folds them in.

---

## PHASE A — SEED (genre-aware questionnaire)

Create + switch the campaign first:

```bash
bash tools/gm-campaign.sh create "<CAMPAIGN_NAME>"
bash tools/gm-campaign.sh switch "<CAMPAIGN_NAME>"
CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
```
(If the name exists: offer switch / rename / recreate.)

Run the questionnaire with **AskUserQuestion**. Ask for: a one-line **premise**
(free text — "Conan but on a drowned coast"), **tone**, **magic level**, and
**setting type** (reuse the classic options). Then ALWAYS ask the **genre bend** —
the single most important anti-generic lever:

Also ask the **voice** question — *"Whose voice should this world be narrated in?"*
— with genre-adaptive suggestions + free text (e.g. sword-and-sorcery → Robert E.
Howard; high fantasy → Tolkien / Le Guin; sci-fantasy → Gibson; whimsical →
Pratchett). Store as `voice_exemplar`. This is what makes narration read like a
real author instead of a generic narrator.

Genre bend options:

- *Sword-and-sorcery (Conan):* magic = blood/curse-priced and villainous; bronze-age
  tech; decadent kingdoms vs. barbarian frontier.
- *High fantasy (Tolkien):* deep lineage/ancestry; a pantheon + old songs; pastoral
  vs. rising dark.
- *Tech / sci-fantasy:* nanomagic or charged tech; infrastructure + corporate/clan
  politics.
- *Folk / cosmic horror:* fragile sanity; small community; a wrongness beneath.

From the answers, **derive an ADAPTIVE axis list** — do NOT use a fixed set. Pick
the axes that are load-bearing for THIS genre and mark each `deep` or `stub`:
- always: `geography`, `factions`, `history`.
- sword-and-sorcery → `magic-lore` (deep, blood/curse), `culture` (oaths/idiom); skip heavy tech.
- tech → `technology` (deep, infrastructure), `factions` (deep, corporate/clan).
- high fantasy → `culture`/`language` (deep, lineage + pantheon), `bestiary`.
- horror → `culture` (the community), `bestiary`/`magic-lore` (the wrongness).

Write `world-seed.json` to the campaign dir:

```json
{
  "premise": "...", "tone": "...", "magic": "...", "setting": "...",
  "genre_bend": "<the distinct commitments, in a sentence or two>",
  "voice_exemplar": "<author/work to channel, e.g. 'Robert E. Howard'>",
  "art_style": "In the style of <a CREATIVE, MULTIFACETED mashup> — e.g. 'In the style of Frank Miller's Batman but rendered in smudged charcoal', 'In the style of a gilded medieval illuminated manuscript but depicting cyberpunk megacities', 'In the style of Studio Ghibli but H.R. Giger biomech'. Combine two unexpected references; aim for the surprise that makes a viewer go OHHHHH. This is the campaign's locked gallery signature, set ONCE here.",
  "chronicler_name": "<the in-world artist who 'makes' every image, fits the tone>",
  "chronicler_persona": "<their voice/bias — grim, sarcastic, reverent, unreliable>",
  "axes": [ { "axis": "geography", "depth": "deep", "bend": "..." },
            { "axis": "magic-lore", "depth": "deep", "bend": "blood-priced curses" },
            { "axis": "bestiary", "depth": "stub", "bend": "..." } ]
}
```

---

## PHASE B — SKELETON (one pass, while the seed is fresh)

YOU (the main GM agent) author the full creative skeleton NOW, in one pass, while
all the seed context is fresh in mind. This is the coherence anchor every parallel
author will carry — get the world's identity right here.

Write `world-bible.json` to the campaign dir with `confirmed: false` and ALL
required keys (validated by `lib/world_bible.py`): `name`, `voice`
(`style`/`vocab`/`sample_passages`), `tone`, `themes`, `factions`

**Author the `voice` block from `voice_exemplar`** — this is how the GM narrates
in the author's voice at play (surfaced every beat by `get_full_context`):
- `style`: a concrete prose fingerprint imitating the exemplar (sentence rhythm,
  diction, imagery) — not "epic fantasy" but e.g. "Howard's terse, muscular cadence;
  sensory violence; archaic but plain diction."
- `sample_passages`: 2-3 SHORT passages YOU write *in that author's voice* (original
  imitation, NOT copied from the real author's text) so the GM has a concrete target.
- `vocab`: a few signature in-world terms.
The `culture` axis (Phase C) may deepen `vocab` + add passages.

Other required keys: `factions`
(`{nodes:[],edges:[]}` — seed the major ones), `geography` (`{nodes,edges}` — the
starting region + a few named places beyond the village), `signature_systems` (the
distinctive magic/tech, named), and a short `timeline`. Make it specific and
distinct — this is the spine, not a stub.

Validate, then present for approval:
```bash
uv run python lib/world_bible.py validate
uv run python lib/world_bible.py show
```

Show the user the `name`, voice style, themes, factions, and signature systems.
**Gate the fan-out on their approval** — let them edit or accept. Do not proceed
until they accept. (The bible stays `confirmed: false` until Phase E.)

---

## PHASE C — FAN-OUT (parallel authors + the kit owner)

Launch ALL of these **simultaneously** as parallel Task calls (like /import's
extractors). One `world-author` per axis in `world-seed.json`, plus one
`world-kit-author`:

```
Task: subagent_type=world-author
prompt: "Author the '<AXIS>' axis (DEPTH=<deep|stub>) for the active campaign.
         Read world-seed.json + world-bible.json (canon). Write ONLY
         canon/<AXIS>.md and authored/<AXIS>.json per your contract. bend: <bend>."
   ... (repeat for every axis) ...

Task: subagent_type=world-kit-author
prompt: "Author ruleset.json for the active campaign from world-seed.json +
         world-bible.json. Derive mechanics from the world; do not default to 5e."
```

Wait for ALL to complete. Each writes its own files only → no collisions.

---

## PHASE D — RECONCILE (anti-drift)

```
Task: subagent_type=world-reconciler
prompt: "Reconcile the active campaign: read world-seed.json, world-bible.json,
         all authored/*.json, canon/*.md, ruleset.json. Run the genericness
         critic, kit↔flavor agreement, and graph cross-link. Write
         reconcile-report.json and apply low-risk cross-link edits."
```

Read `reconcile-report.json`. If `verdict: needs-changes`, apply the rewrites /
kit patches (re-run the relevant `world-author` / `world-kit-author`, or edit the
authored files), then re-reconcile. Surface generic flags + kit disagreements to
the user if judgment is needed.

---

## PHASE E — GROUND (consolidate → embed → confirm → open it alive → validate)

```bash
# 1. Fold authored contributions into runtime state + the bible (serial, race-free)
#    — locations, npcs, PLOTS, facts. Check the report's plot count is non-zero:
#      everything in step 5 reads plots.json.
bash tools/gm-worldgen.sh consolidate

# 2. Compile authored canon into one document
CANON=$(bash tools/gm-worldgen.sh compile-canon --json | uv run python -c "import sys,json;print(json.load(sys.stdin)['data']['path'])")

# 3. Embed it for RAG — same path imports use (writes current-document.txt + chunks + vectors)
bash tools/gm-extract.sh prepare "$CANON" "<CAMPAIGN_NAME>"

# 4. Confirm the bible (the human approved it in Phase B; world is now grounded)
uv run python -c "import sys; sys.path.insert(0,'lib'); from world_bible import WorldBible; WorldBible().confirm()"
```

**5. Open the world ALIVE** — the same four passes an import runs, so the first
`/gm` beat has story threads, a spine, live pressure and a place to stand instead of
an empty context and a null location:

```bash
set -e   # each pass feeds the next; a failure must stop the chain here

# Derive campaign_rules from the bible's signature_systems (the kit itself was
# authored by world-kit-author in Phase C — this is the systems block
# WorldKit.campaign_rules() reads into every scene context).
bash tools/gm-extract.sh campaign-rules

# Order matters: spine FIRST. seed-clocks and seed-opening both read the arc it
# writes (overview.story_spine + the plots it sequenced).
bash tools/gm-extract.sh spine "<CAMPAIGN_NAME>"          # arc order + through-line
bash tools/gm-extract.sh seed-clocks "<CAMPAIGN_NAME>"    # threat clocks from countdown plots
bash tools/gm-extract.sh seed-opening "<CAMPAIGN_NAME>"   # starting location + opening beat + log hook
```

**If a pass fails, STOP** and fix it before play — do not carry on to Phase F.
The two real failures, both upstream in the authored world:
- `spine` prints an empty arc, or `seed-opening` reports "no main/spine plot to
  open on" → no axis authored a `main` plot. Add one to the relevant
  `authored/<axis>.json` and re-run `consolidate` + this whole block.
- `campaign-rules` writes a thin block → the bible's `signature_systems` are thin.
  Fix them in `world-bible.json` (the bible stays the single source) and re-run.

`seed-clocks` seeding zero clocks is NOT a failure — it means no plot named an
explicit countdown. Add one to a `threat` plot's description if the world should
have a ticking clock.

Then run **`/world-check`** (or `uv run python lib/schemas.py`) to validate the
generated world. Fix anything it flags before play.

---

## PHASE F — OVERVIEW, SESSION LOG, HANDOFF

**Lock the chronicler + art style NOW** (the gallery signature is a world-creation
decision, not an in-play improvisation) from the seed's `art_style` /
`chronicler_*` fields:

```bash
bash tools/gm-image.sh chronicler \
  --name "<chronicler_name>" \
  --style "<art_style — MUST start with 'In the style of ...'; a creative, multifaceted mashup>" \
  --persona "<chronicler_persona>"
```

The `scene-illustrator` agent READS this locked style and opens every prompt with
it — it never picks its own. Make the mashup genuinely surprising. This single
chronicler record carries BOTH halves of the image identity — the **art style**
(`--style`) and the **art narrator** (`--name` / `--persona`, the in-world entity
who "makes" every picture). Lock both now; they never change in play.

**Author a `visual_appearance` block for every notable NPC** (and the PC at
`/create-character`). It is the locked look every future image renders, with
EXACTLY these 11 keys: `sex, age, race, species, hair, face, eyes, clothing,
gear, demeanor, size`. Ground each field in the source/bible; leave unknowns "".
Set them in batch as the world consolidates:
```bash
bash tools/gm-npc.sh set-appearance "<NPC name>" \
  --sex "..." --age "..." --race "..." --species "..." --hair "..." \
  --face "..." --eyes "..." --clothing "..." --gear "..." --demeanor "..." --size "..."
```
(Extracted/imported NPCs already carry the empty block from `NPC_SCHEMA` — fill it.)

Update `campaign-overview.json` (date/time, `session_count: 0` — Phase E's
`seed-opening` already set `player_position.current_location`; only override it if
the arc's opening location is wrong) and append the world summary to
`session-log.md` (starting location, key NPCs, the three plot tiers) alongside the
opening hook `seed-opening` wrote. Then display a summary box and hand off:

```
Your world awaits its hero. Who are you in this world?
```

Then ask that **one question** — identity first, mechanics later — and offer three doors:

- **someone from this world** → `bash tools/gm-player.sh onboard canon "<NPC name>"`.
  An original world's canon door draws from the NPCs the axis authors just wrote, so name a
  few of them (their sheet and their canonical voice come along).
- **someone of their own** → `bash tools/gm-player.sh onboard original "<name>" "<one-line concept>"`
- **no one yet** → `bash tools/gm-player.sh onboard nameless`

Persist the answer and open the scene. `/create-character` remains the **opt-in** full
builder for a player who wants to roll a sheet properly — offer it, don't impose it.

---

## COMPLETION CHECKLIST
- [ ] `world-seed.json` with an adaptive axis list
- [ ] `world-bible.json` authored in one pass, approved, `confirmed: true` after grounding
- [ ] `ruleset.json` World Kit (non-5e-default, derived from the world)
- [ ] every axis produced `canon/<axis>.md` + `authored/<axis>.json`
- [ ] `reconcile-report.json` verdict handled
- [ ] consolidated `locations/npcs/plots/facts.json` + merged bible graphs
- [ ] `current-document.txt` embedded (RAG returns hits)
- [ ] world opens alive: `campaign_rules` on the overview, a non-empty `story_spine`,
      threat clocks seeded (or knowingly none), `player_position.current_location` set
- [ ] `/world-check` passes
- [ ] chronicler locked (`gm-image.sh chronicler`) — both the art **style** (starts "In the style of ...", a creative mashup) AND the art **narrator** (name + persona)
- [ ] every notable NPC has a `visual_appearance` block (11 keys); PC gets one at `/create-character`
- [ ] overview + session log set; handed off to the one question (`gm-player.sh onboard ...`)

## ERROR RECOVERY
- Campaign exists → switch / rename / recreate.
- An author returns empty/invalid → re-launch just that axis.
- Bible fails validation → fix the missing required key, re-validate before fan-out.
- `prepare` finds no text → confirm `compile-canon` wrote a non-empty file.
