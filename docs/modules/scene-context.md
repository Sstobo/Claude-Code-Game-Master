---
type: Module
title: Scene context — the two doors
description: What the harness pushes to the model each beat, and why "context" means two different things depending on which tool you call.
sources:
  - { resource: /lib/session_manager.py }
  - { resource: /lib/world_kit.py }
  - { resource: /lib/scene_context.py }
  - { resource: /lib/search.py }
  - { resource: /lib/entity_manager.py }
  - { resource: /tools/gm-context.sh }
  - { resource: /lib/play_pack.py }
generated: { by: claude-opus-4-8[1m], at: 2026-08-16T00:00:00Z }
verified: { by: claude-fable-5, at: 2026-08-14T12:19:52Z }
---

# Scene context — the two doors

This is the mechanism the whole product rests on: instead of hoping the model remembers,
the harness *pushes* the campaign at it every beat. Two different commands both call
themselves "context" and return almost disjoint things. Calling the wrong one is the
most common way a beat comes out flat.

| Command | Code | Returns |
|---|---|---|
| `gm-session.sh context` | `SessionManager.get_full_context` (`lib/session_manager.py:592`) | The **session brief** — everything below, as formatted prose for the model |
| `gm-context.sh ["loc"]` | `SceneContext.build` (`lib/scene_context.py:37`) | The **place brief** — this location, NPCs present, named entities, plus grounded source passages |

Neither contains the other. The session brief has no source passages; the place brief has
no history, threads, clocks, voice, or rules. Narrating a scene generally wants both.

## What the session brief carries, and why each block exists

`get_full_context` (`lib/session_manager.py:592`) assembles, in order: header (campaign, session #, location, time) ·
**KIT** · **PRIMER** (play pack, when set) · play style (pacing, action menu, player-rolls dice, RAG inspiration) · **failure (one informing sentence)** · scene-image gate + chronicler · **narrative voice** · **world index** ·
**previously on** + where-we-paused + open threads · **the world remembers** · story threads · **ready threads** (dormant seeded plots whose linked NPC/place is now present, or whose clock matured) · key facts · threat
clocks · character · party members · **NPC voices** · pending consequences · **your
world's rules** · **signature systems** (executable kit primitives — `WorldKit.systems()`,
rendered "ROLL these", distinct from the prose rules block).

Eight of those blocks carry design decisions that are not obvious from reading them:

- **KIT is ambient so skills do not re-derive it.** It sits right under the campaign
  header and names kit identity, resolution, progression, vitals, and skills, loaded
  via `WorldKit(world_state_dir)`. A missing `kit` field reads as `custom` — DCC's
  fixture is that case. If `WorldKit` cannot load (no active campaign, a throw), the
  block is skipped rather than crashing the brief. `gm-combat` / `gm-levelup` /
  `gm-spellcasting` defer to this block instead of calling `world_kit.py info`.

- **PRIMER is tonight's table.** When `campaign-overview.json.play_pack` has any
  field set, `render_primer` appends `--- PRIMER ---` (whose story, this room,
  who is here, the hook, what is offstage). An empty pack adds nothing. Setting
  a pack does not fabricate a session. New names walk on via
  `gm-playpack.sh from-book`.

- **Play-style flags stay; failure is one informing sentence.** Pacing, dice, action
  menu and inspiration still read `preferences` and surface when set. Failure is
  appended unconditionally — a single reminder that failure should cost something
  and the stake is decided before the roll — not a NEVER-list or persist-command
  sermon. Numeric caps and adjudication judgment live in skills / `gm-craft`, not
  in the always-on brief. The opt-in `tight` beat-length preference is the exception
  that still injects its own cap, because the player asked for it.

- **Narrative voice is a prose target, not lore.** The block is labelled that way in the
  output for a reason — the sample passages are style exemplars to imitate, and a model
  that treats them as world facts will narrate someone else's scene.
- **WORLD INDEX is the roster the GM scans before inventing a name.** Built from the
  bible's `index` (`npcs`/`locations`/`items`/`monsters`), it lists `name — note` lines
  grouped by non-empty bucket. It is emitted only when at least one bucket has an entry;
  an absent or all-empty `index` prints no header at all.
- **NPC secrets are surfaced by existence only.** `lib/session_manager.py:932` prints
  `"has a secret"` and never the secret text, so a secret can sit in `npcs.json` without
  leaking into narration the moment its owner walks on stage.
- **Presence does not require a voice, and present NPCs carry their memory.** Who is here
  is `npcs_present` (party always, plus exact location tag — see below). `_present_npcs`
  only slices voice lines onto that set, and still returns an NPC with no extracted
  dialogue — it used to `continue` past them, which made every stubbed and original-world
  NPC invisible while standing in the room. Each present NPC's recent `events` render
  under their entry (`_recent_events`, shared with the party block so history looks the
  same wherever a character appears; party members render theirs once, in the party block).
  This is the wire that lets an NPC act like they remember what the player did to them —
  the write side is `gm-npc.sh update "<name>" "<event>"`. On top of that, `_npc_anchored_facts`
  re-scans the whole global facts log each build and surfaces — as `remembers:` sub-lines under
  a present, non-party NPC — any fact whose text NAMES them (a `gm-note.sh` fact that only lands
  in `facts.json` would otherwise never reach them). Matching is on a word boundary against the
  full NPC key and any explicit `aliases` entry only, so "Ana" does not fire on "Banana" and a
  common leading token ("Old" in "Old Man Withers") never attaches ordinary lowercase prose;
  hits already in PREVIOUSLY ON, THE WORLD REMEMBERS, or the NPC's own `events` are
  dropped so nothing shows twice. It is read-time only — no write-side coupling, so per-NPC
  memory is not lost to the global log without a duplicate copy in storage.
- **THE WORLD REMEMBERS is the harness asking recall on the GM's behalf.** `CampaignMemory`
  was a complete long-term memory with no automated reader — recall only ever fired if the
  GM thought to ask, which needs the GM to already suspect there is something to remember.
  `_world_remembers` builds the query from the scene itself (current location + present NPC
  names), and adds `open_debts` from the latest arc entry. It returns empty on *any* failure
  (no memory file, no embedding deps, a half-written index), so a broken memory costs the
  brief nothing mid-session. It also drops hits that repeat PREVIOUSLY ON, because
  `recall()` falls back to re-gathering the same session log.
- **Truncated lists disclose their remainder.** Tight bounds exist so the brief stays a
  brief — story threads 6, facts 3/category, previously-on 3, pending 10, party 8, NPC
  voice lines 4, vocab 12, sample passages 3, world-remembers 3. `--full` lifts them.
  Each truncation prints `+N more <noun> — <how to see the rest>` rather than dropping
  the tail silently. YOUR WORLD'S RULES is never truncated and never gets a remainder
  pointer.
- **World rules prefer kit `signature_systems`, then `campaign_rules`, and are never
  truncated.** Every other block is bounded — by item count, not by chopping an entry
  mid-sentence — but YOUR WORLD'S RULES is printed whole (`lib/session_manager.py:997`).
  A kit that declares `signature_systems` (list or the Conan dict form) is the live
  surface; a legacy campaign with none still gets `campaign_rules`. Those rules *are*
  the magic that makes each book distinct, and the GM is told to follow them exactly, so
  it must see all of them. See [game core and World Kit](game-core-and-world-kit.md).

`--full` lifts every bound. `DM_DEBUG_CONTEXT=1` prints an approximate token count to
stderr without changing the output; the ~2k-token target it reports against is guidance,
never a cut.

## RAG is optional everywhere, and fails to empty

`SceneContext.build` wraps the entire enhancer call in a bare `except Exception: pass`
(`lib/scene_context.py:56-64`). A campaign with no vector store, a missing `chromadb`, or
a runtime error inside the enhancer all produce the same thing: `passages: []` and
`rag_available: false`. Play continues on world state alone.

The cost of that choice: **a broken RAG install is indistinguishable from a campaign that
was never vectorized.** Neither logs. If passages are unexpectedly empty, check
`rag_available` in `gm-context.sh --json`, then confirm the campaign actually has vectors
rather than assuming the import worked. See [RAG stack](rag-stack.md).

## Which search tool

`gm-search.sh` is the free-text door and takes a mode flag: `--world-only`, `--rag-only`,
or neither for both. `gm-enhance.sh query` is **not** a search — it takes an entity *name*.
Reaching for it with a free-text phrase returns nothing and looks like an empty world.

Who is here is one helper, `npcs_present` (`lib/entity_manager.py`): party members
always, everyone else by case-insensitive **exact** equality of the current location
against a `tags.locations` entry. Both context doors and consequence tick call it.
Substring was the place-brief bug — "The Inn" must not count as "The Inner Sanctum",
and an untagged party member must still stand in the room. CLI `gm-search.sh
--tag-location` / `--tag-quest` may still substring-search for discovery; that is not
presence. The field those tags live in used to have two spellings — see
[the NPC location tag split](../gotchas/npc-location-tag-split.md).

## Related

- [Campaign memory](campaign-memory.md) — where "previously on" is built from
- [Living world](living-world.md) — clocks and consequences that appear in the brief
- [A play turn](../flows/play-turn.md) — where in the loop each door is called
