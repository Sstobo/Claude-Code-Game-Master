---
type: Module
title: World state JSON schema reference
description: The on-disk shape of every per-campaign file — the contract no single source file states.
sources:
  - { resource: /lib/schemas.py }
  - { resource: /lib/minor_stubs.py }
  - { resource: /lib/npc_manager.py }
  - { resource: /lib/extraction_cap.py }
  - { resource: /lib/location_reconcile.py }
  - { resource: /lib/consequence_manager.py }
  - { resource: /lib/world_kit.py }
  - { resource: /lib/world_bible.py }
  - { resource: /lib/session_manager.py }
  - { resource: /lib/play_pack.py }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T16:22:00Z }
verified: { by: claude-fable-5, at: 2026-08-13T14:27:33Z }
---

# World State JSON Schema Reference

The on-disk shape of a campaign, which no single source file declares — the managers each
write their own slice. **`lib/schemas.py` is the authority on every enum below**; where
this document lists allowed values it is a convenience copy, and the copy has drifted
before. Re-derive with `uv run python lib/schemas.py` (validates the active campaign) or by
reading the `VALID_*` / `PLOT_TYPE*` sets at the top of that file.

---

## Campaign Structure

Each campaign lives in its own folder: `world-state/campaigns/<name>/`. The active campaign
is named in `world-state/active-campaign.txt`.

```
<campaign-name>/
├── campaign-overview.json   # Campaign settings, player position, campaign_rules
├── character.json           # Player character sheet (FLAT shape)
├── npcs.json                # All NPCs
├── locations.json           # All locations
├── facts.json               # World facts by category
├── plots.json               # Plot hooks and quests
├── items.json               # Items (from imports)
├── consequences.json        # Pending/resolved events + firing provenance
├── ruleset.json             # World Kit — how this world plays
├── world-bible.json         # Fidelity spine (voice, factions, geography, systems)
├── rules.md                 # Optional long-form rules prose (ruleset.rules_doc)
├── session-log.md           # Session history — the canonical ledger
├── threat-clocks.json       # Named pressure clocks (optional)
├── campaign-memory.json     # Recall index, rebuilt on save
├── chronicler.json          # Locked art style + in-world artist
├── world-tick-log.json      # Between-session tick provenance
├── loremaster-cache.json    # Per-location grounded briefs
├── saves/                   # Snapshot saves
├── fallen/                  # Archived sheets of dead PCs
├── images/                  # Generated scene images + _gen-log.jsonl
├── chunks/ · vectors/       # RAG source chunks and the ChromaDB index
└── extracted/               # Legacy census-import staging
```

Most of these are created lazily — a campaign that has never been illustrated has no
`chronicler.json`, and one that was never imported has no `vectors/`.

---

## campaign-overview.json

```json
{
  "campaign_name": "string",
  "genre": "Fantasy",
  "tone": {
    "horror": 30,
    "comedy": 30,
    "drama": 40
  },
  "current_date": "string (in-game date)",
  "time_of_day": "dawn|morning|midday|afternoon|dusk|evening|night|midnight",
  "player_position": {
    "current_location": "string or null",
    "previous_location": "string or null",
    "arrival_time": "ISO timestamp"
  },
  "current_character": "string (character name)",
  "session_count": 0,

  "campaign_rules": {
    "description": "…runs on its own systems — follow them exactly.",
    "signature_systems": ["the book's distinctive mechanics"],
    "tone": "string"
  },
  "story_spine": {"arc": ["ordered plot names"], "through_line": "string"},
  "preferences": {"action_menu": true, "rag_inspiration": true},
  "play_pack": {
    "whose_story": "string",
    "room": "this room, not a kingdom",
    "present": ["names in the room"],
    "exits": ["what you can see from here"],
    "hook": "the problem that will not wait",
    "offstage": ["horizon names — do not build"],
    "primer": "one short GM paragraph"
  },
  "opening_hook": {"location": "string", "hook": "string"}
}
```

**`campaign_rules` is the block that reaches the model verbatim and untruncated** every
beat — it is where a world's signature systems must live to have any effect. Putting them
in `ruleset.json` instead is a silent no-op for narration. See
[game core and World Kit](modules/game-core-and-world-kit.md). Worlds are free to add
their own keys here (the shipped DCC fixture carries `viewer_stats`, `pending_boxes`, and
`pending_interview_topics`).

**`play_pack` is tonight's table**, not a gazetteer. `lib/play_pack.py` writes it;
`get_full_context` renders a `--- PRIMER ---` block when any field is set. `stage`
persists the room, present NPCs, and exit stubs into the journal. `from-book` writes
exactly one name when play walks toward it. Setting a pack must not fabricate a
session (`### Session Ended`). See [the dream](conventions/the-dream.md).

---

## npcs.json

A dictionary keyed by NPC name.

```json
{
  "NPC_NAME": {
    "description": "string (physical/personality description)",
    "attitude": "ally|neutral|enemy|friendly|hostile|suspicious|helpful",
    "created": "ISO timestamp",
    "events": [
      {"event": "string describing what happened", "timestamp": "ISO timestamp"}
    ],
    "tags": {
      "locations": ["location name"],
      "quests": ["quest name"]
    },
    "context": ["canonical voice lines — verbatim source dialogue"],
    "enhanced": false,
    "enhanced_at": "ISO timestamp",
    "background": true,
    "is_party_member": false,
    "became_pc": false,
    "character_sheet": null,

    "aliases": ["name variants recorded by the integrity gate"],
    "visual_appearance": {"sex": "", "age": "", "race": "", "species": "", "hair": "",
                          "face": "", "eyes": "", "clothing": "", "gear": "",
                          "demeanor": "", "size": ""},
    "goal": "string", "secret": "string", "current_mood": "neutral",
    "voice": "string — how they SOUND (not their lines; those are `context`)",
    "bonds": {},
    "stats": {"ac": null, "hp": 45, "cr": 3, "difficulty": "minion|standard|boss",
              "statless": false}
  }
}
```

Notes:

- **`context` vs `voice`** are routinely confused — `context` holds quotable lines;
  `voice` describes the sound. See [NPC model](modules/npc-model.md).
- **`tags.locations` is the only location field** (since 2026-08-13). A campaign imported
  earlier may still carry a legacy `location_tags` — migrate with
  `gm-npc.sh unify-tags`. See [the tag-split gotcha](gotchas/npc-location-tag-split.md).
- **`background: true` is the import's entity tier** (`extraction_cap`), present on
  npcs, locations, items and plots alike. It marks everything the importance ranking
  put below the top-N — a real entity the book named, kept whole on disk, just not part
  of the playable core. Absent means active; the key is omitted rather than set false.
  It changes three things: `gm-enhance.sh batch` skips these entities (a RAG round-trip
  each); `gm-npc.sh promote` clears the flag, because a party member is active by
  definition; and a background **plot** is left out of the scene context's STORY THREADS
  and of `gm-plot.sh threads`, which discloses how many it held back. It does **not**
  gate an NPC's presence in a scene — that is decided by `tags.locations` against the
  party's location, for background and active NPCs alike.

`attitude` values above are the `VALID_ATTITUDES` set in `lib/schemas.py`; an invalid
attitude is coerced to `neutral` on batch import rather than rejected.

### Party Member Character Sheet

When `is_party_member: true`, the `character_sheet` contains:

```json
{
  "character_sheet": {
    "race": "Human",
    "class": "Fighter",
    "level": 2,
    "hp": {
      "current": 18,
      "max": 22
    },
    "ac": 14,
    "stats": {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 11, "cha": 10},
    "saves": {"str": 4, "dex": 1, "con": 3, "int": 0, "wis": 0, "cha": 0},
    "skills": {},
    "attack_bonus": 4,
    "damage": "1d8+2",
    "equipment": ["Longsword", "Shield", "Chain Shirt"],
    "features": ["Second Wind", "Fighting Style (Defense)"],
    "conditions": [],
    "xp": 0
  }
}
```

**HP Tracking:** Party members use `hp.current` and `hp.max`. Update with:
```bash
bash tools/gm-npc.sh hp "Name" -5   # Damage
bash tools/gm-npc.sh hp "Name" +3   # Heal
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| description | Yes | Character description |
| attitude | Yes | One of the supported attitude values |
| created | Yes | ISO timestamp when created |
| tags | No | Object with `locations` and `quests` arrays |
| events | No | Array of event objects |
| context | No | Source passages for RAG enhancements |
| enhanced | No | Flag when RAG enhancements applied |
| enhanced_at | No | ISO timestamp when enhanced |
| is_party_member | No | True if NPC is a party member |
| character_sheet | No | Full character sheet if party member (see above)

---

## locations.json

A dictionary keyed by location name.

```json
{
  "LOCATION_NAME": {
    "position": "string (relative position, e.g. 'north of town')",
    "description": "string (what the place looks like)",
    "connections": [
      {"to": "Other Location", "path": "rocky trail"}
    ],
    "discovered": "ISO timestamp",
    "notes": "optional string",
    "source": "optional string",
    "background": true,
    "low_confidence": true
  }
}
```

Notes:

- **`low_confidence: true` marks a reconcile stub** (`location_reconcile`): the source
  referenced this place from a plot, an NPC tag, or a connection, but no extractor
  produced a node for it, so the import created one and wired it to the most-connected
  hub. The flag says the name is the book's and everything else is a guess — flesh it
  out in play. These nodes also carry `source: "auto-stub"` and a `notes` line saying so.
- **`background: true`** on a location is the same entity tier described under
  [npcs.json](#npcsjson).

### Dungeon Rooms (Extended Schema)

Dungeon rooms (stored in `locations.json`) may include:

```json
{
  "ROOM_NAME": {
    "dungeon": "string (dungeon name)",
    "room_number": 1,
    "description": "string",
    "exits": {
      "north": {"to": "Room 2", "type": "open|door|secret|stairs-up|stairs-down"}
    },
    "state": {"discovered": false, "visited": false, "cleared": false}
  }
}
```

---

## facts.json

A dictionary with category keys, each containing an array of fact **objects**.

```json
{
  "world_building": [
    {"fact": "The kingdom has been at peace for 100 years",
     "timestamp": "2026-01-28T21:50:30Z"}
  ],
  "session_events": [
    {"fact": "The party met the king on day 1", "timestamp": "..."}
  ]
}
```

Bare strings are tolerated on read (`lib/campaign_memory.py:60` falls back to `str(it)`)
but managers write the object form.

**Category names are load-bearing.** `campaign_memory` classifies a fact as book-canon
only when its category is `plot_world` or `world_building`; everything else is filed as
our-story. See [campaign memory](modules/campaign-memory.md).

### Common Categories

- `world_building` - Established world facts
- `session_events` - What happened this session
- `plot_local` - Local storyline facts
- `plot_regional` - Broader mystery/conspiracy facts
- `plot_world` - World-shaking revelations
- `player_choices` - Key decisions made
- `npc_relations` - How NPCs feel about the party
- `dropped_references` - Import provenance: place references `location_reconcile` could
  not turn into a node (a connection's routing rule, or a blank). Written by the import,
  not by play — it exists so a discarded name is recoverable instead of stdout-only.

---

## consequences.json

Tracks events that will trigger in the future.

```json
{
  "active": [
    {
      "id": "8-char-uuid",
      "consequence": "string (what will happen)",
      "trigger": "string (free-text, when it triggers)",
      "created": "ISO timestamp",

      "trigger_type": "on_location | on_npc | on_time | on_event   (OPTIONAL, structured)",
      "match": "string compared against world state (location name / npc / time keyword / event keyword)",
      "expiry": "string date or condition after which it ages out   (OPTIONAL)"
    }
  ],
  "resolved": [
    {
      "id": "8-char-uuid",
      "consequence": "string",
      "trigger": "string",
      "created": "ISO timestamp",
      "resolved": "ISO timestamp",
      "expired": "ISO timestamp (when aged out rather than resolved)"
    }
  ],

  "provenance": [
    {"id": "…", "consequence": "…", "reason": "why it matched",
     "ctx_key": "location|time|date", "fired_at": "ISO timestamp"}
  ],
  "_snapshot": {"active": [], "resolved": []}
}
```

A fired consequence also carries `last_fired_key` (the scene key that fired it) and stays
in `active` — firing is not resolving. `_snapshot` is the **one-beat** rollback buffer,
overwritten by the next tick. See [the living world](modules/living-world.md).

**Structured triggers** (`trigger_type`/`match`/`expiry`) are additive and
optional. When present, the reactivity engine fires the consequence automatically
when world state matches (and expires it past `expiry`); when absent, the
consequence is a legacy free-text entry matched fuzzily. A campaign may mix both.

---

## plots.json

A dictionary keyed by plot name.

`type` comes from the single canonical taxonomy, `schemas.PLOT_TYPES` — derived from
`schemas.PLOT_TYPE_SORT`, whose ranks are also the display/sort order for STORY THREADS
and plot listings. `validators`, `minor_stubs`, `plot_manager` and `session_manager` all
import it; there is no second copy. `minor_stubs.validate_plot_types` (the `/import`
validate step) passes canonical types through untouched, maps extractor synonyms
(`quest`→`side`, `arc`→`main`, `conflict`→`threat`, …) via `PLOT_TYPE_SYNONYMS`, and only
falls back to `side` — with a warning naming the original — for a type it does not know.

```json
{
  "PLOT_NAME": {
    "type": "main|threat|mystery|side|personal|world|optional|scene|theme|idea|lore|background|other",
    "status": "active|completed|failed|dormant|available",
    "sequence": 1,
    "depends_on": ["earlier plot name"],
    "description": "string (what the quest is about)",
    "npcs": ["involved", "npc", "names"],
    "locations": ["relevant", "locations"],
    "objectives": ["optional objective strings"],
    "rewards": "optional string",
    "consequences": "optional string",
    "events": [
      {"event": "progress update", "timestamp": "ISO timestamp"}
    ],
    "completed_at": "ISO timestamp or null",
    "failed_at": "ISO timestamp or null"
  }
}
```

---

## items.json

A dictionary keyed by item name. Typically populated by `/import`.

```json
{
  "ITEM_NAME": {
    "name": "string",
    "description": "string",
    "type": "weapon|armor|potion|scroll|wondrous|treasure|equipment|prop|artifact",
    "rarity": "common|uncommon|rare|very rare|legendary|artifact",
    "mechanics": "optional string",
    "value": "optional string",
    "location": "optional string",
    "attunement": false,
    "cursed": false,
    "source": "optional string"
  }
}
```

---

## character.json

The player character sheet, in the **flat** canonical shape. `stats` is an open,
kit-defined dict — the six abilities below are a D&D example, not a requirement. A legacy
open-schema file (`identity`/`vitals`/`attributes`) is migrated to flat on first read.
See [the player character sheet](modules/player-character.md).

```json
{
  "name": "string",
  "race": "string",
  "class": "string",
  "level": 1,
  "background": "string",

  "stats": {
    "str": 10,
    "dex": 10,
    "con": 10,
    "int": 10,
    "wis": 10,
    "cha": 10
  },

  "hp": {"current": 10, "max": 10},

  "ac": 10,
  "skills": {},
  "saves": {"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0},

  "equipment": ["item", "names"],
  "features": ["class", "features"],
  "background": "string",
  "alignment": "string",
  "bonds": "string",
  "flaws": "string",
  "ideals": "string",
  "traits": "string",
  "notes": [],
  "gold": 0,
  "xp": {"current": 0, "next_level": 300},

  "conditions": [],
  "status": "alive | dying | dead",
  "died_at": "ISO timestamp (set by gm-player.sh kill)",
  "cause": "string",
  "visual_appearance": {"…11 fixed fields — see lib/visual_appearance.py"},
  "origin": "canon | original | nameless",
  "concept": "string (original mode)",
  "voice": ["canonical lines, when lifted from a canon NPC"],
  "current_location": "string",
  "id": "string"
}
```

`xp` accepts a bare integer and is normalized to `{current, next_level}` on load. Kit
vitals a schema has never heard of (`water`, `heat`, `corruption`) live at the top level
and survive the flat↔open round trip.

---

## Save Files (saves/*.json)

A named point-in-time copy of **live campaign state**, not of derived indexes.
`SessionManager.create_save` writes `{YYYYMMDD-HHMMSS}-{name}.json` under `saves/`;
a same-second collision uniquifies the filename instead of overwriting.

**Versioned (`save_version: 1`).** Snapshot keys are campaign filenames plus the
`characters` helper (the PC sheet, keyed `character`) and `fallen/<file>.json`.
JSON values are objects; markdown values are strings. A file that is not on disk
is omitted — never stubbed as `{}`. Restore writes only keys the snapshot has.

Skipped (derived, staging, or the save dir itself): `chunks/`, `vectors/`,
`images/`, `extracted/`, `canon/`, `authored/`, `loremaster-cache.json`, `saves/`.

Combat lives in `combat_state.json` (the file `CombatManager` actually writes).

**Autosaves.** A save whose name is `autosave` (the Stop hook) keeps the newest
`AUTOSAVE_KEEP` (3) matching files; named manual saves are not rotated.
`_find_save("autosave")` returns the newest remaining autosave.

**Legacy (no `save_version`).** Snapshot used underscored keys covering six files
(`campaign_overview`, `npcs`, `locations`, `facts`, `consequences`, `characters`).
Restore still applies those six, then prints a partial-restore warning naming
contract files the snapshot did not include. Present-time plots, clocks, and
items otherwise stay mixed in — do not treat a legacy save as a whole-world revert.

```json
{
  "save_version": 1,
  "name": "string (save name)",
  "created": "ISO timestamp",
  "session_number": 5,
  "snapshot": {
    "campaign-overview.json": {},
    "npcs.json": {},
    "locations.json": {},
    "facts.json": {},
    "plots.json": {},
    "items.json": {},
    "consequences.json": {},
    "ruleset.json": {},
    "world-bible.json": {},
    "threat-clocks.json": {},
    "campaign-memory.json": {},
    "chronicler.json": {},
    "world-tick-log.json": {},
    "combat_state.json": {},
    "rules.md": "text...",
    "session-log.md": "text...",
    "fallen/hero.json": {},
    "characters": { "character": {} }
  }
}
```

---

## Validation Notes

- All timestamps use ISO 8601 format with timezone
- Entity names serve as dictionary keys (case-sensitive)
- Empty arrays `[]` are preferred over `null` for list fields
- Boolean fields default to `false` if omitted
- The `created` field is auto-set by managers when entities are created

## ruleset.json (World Kit)

Per-campaign ruleset that drives play through the generic `game_core`. Declares
how a world plays without baking in D&D 5e.

```json
{
  "name": "Dungeon Crawler Carl",
  "kit": "custom | dnd5e   (absent = custom; dnd5e unlocks the D&D mechanics skills + dnd5eapi)",
  "stat_schema": { "attributes": ["str","con","dex","int"], "vitals": ["hp"] },
  "progression": { "model": "milestone | xp-levels | resource-axis", "...": "model config (thresholds/tiers/resource)" },
  "resolution": { "model": "d20-vs-dc" },
  "lethality": { "model": "death-saves | gritty | none", "massive_damage_at": 20 },
  "systems": [ {"primitive": "named_track|price_roll|reaction_roll|guarded_payoff", "name": "Menace", "config": {}} ],
  "active_agents": ["monster-manual", "loot-dropper"],
  "rules_doc": "rules.md"
}
```

- `lethality` (optional; absent = `death-saves`, the 5e default) tunes
  `game_core.classify_harm` via `WorldKit.lethality()`: `gritty` makes 0 HP death
  (no saves), `massive_damage_at` lowers the instant-death overkill bar.
- `systems` (optional) instantiates the `game_core` signature-system primitives
  (`WorldKit.systems()`); each rides scene context as an executable ROLL-these
  block. Written by `book_bible.write_systems` (`gm-extract.sh write-systems`).

- `stat_schema.attributes` is open and kit-defined (no fixed six abilities).
- `progression.model` selects one of the core's three models; its config
  (`thresholds` for xp-levels, `resource`+`tiers` for resource-axis) is supplied here.
- World-flavor systems (loot boxes, viewers) stay in campaign-overview `campaign_rules`.

## world-bible.json (Book Bible)

The structured fidelity spine of a world, loaded at session start. Auto-drafted at
import; captures what makes a book feel like itself.

```json
{
  "name": "string",
  "voice": { "style": "string", "vocab": ["..."], "sample_passages": ["..."] },
  "tone": "string",
  "themes": ["..."],
  "factions":  { "nodes": [{"id","name"}], "edges": [{"from","to","relation"}] },
  "geography": { "nodes": [{"id","name"}], "edges": [{"from","to","adjacency"}] },
  "timeline": ["..."],
  "signature_systems": ["..."],
  "index": {
    "npcs":      [{"name": "string", "note": "one sentence"}],
    "locations": [{"name": "string", "note": "one sentence"}],
    "items":     [{"name": "string", "note": "one sentence"}],
    "monsters":  [{"name": "string", "note": "one sentence"}]
  }
}
```

`index` is the named-entity roster — the things the book already named, one sentence each
— scaffolded empty by `draft-bible` and surfaced as the scene-context WORLD INDEX block so
the GM reuses an established name before inventing one. It is optional (absent on legacy
bibles); when present, `validate_bible` requires the four buckets to be lists of
`{"name","note"}` objects. `segment_into_chapters` still splits the source, but now only
feeds the RAG coarse index (`lib/rag/coarse_index.py`) — it no longer writes into the
bible.

Required: name, voice, tone, themes, factions (graph), geography (graph),
signature_systems. The bible auto-generates the World Kit ruleset + campaign_rules.

A `confirmed: false` flag on a freshly auto-drafted bible holds the world for human review;
**an absent flag counts as confirmed**, so hand-authored and legacy bibles are playable
immediately. See [the World Bible](modules/world-bible.md).

---

## Related

- [The entity graph](modules/entity-graph.md) — why these files cross-reference by name
- [Extraction schema is not the runtime schema](gotchas/extraction-vs-runtime-schema.md)
- [Importing a book](flows/import-a-book.md) — how these files get populated
