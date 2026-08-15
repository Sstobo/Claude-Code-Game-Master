---
slug: world-index
title: World Index — a scannable roster of what exists
status: active
version: 1
createdAt: 2026-08-15T15:16:16Z
updatedAt: 2026-08-15T15:16:16Z
---

## Problem Statement

`world-bible.json` carries a `chapters` array that is pure noise: 126 entries
whose "titles" are random mid-sentence fragments of the source book (page
markers, copyright lines, dialogue scraps). It is produced by
`segment_into_chapters()` slicing the text into 20k-char blocks and grabbing the
first line of each — the boundaries land mid-sentence, so every title is
garbage. Worse, nothing ever reads it: the scene-context assembler loads the
bible but only pulls `voice`, so `chapters` is dead data that has never reached
the GM.

The GM therefore has no *menu* of what actually exists in the world. To bring a
new face or place into a scene it must either guess a name or blind-query RAG.
There is no cheap, in-context list that says "these are the real, named things
you can reach for right now."

## Solution

Replace `chapters` with an `index`: a curated, in-context roster of the named
entities that actually exist in the world, one sentence each, grouped into
npcs / locations / items / monsters. It lives in `world-bible.json` and rides
into scene context every session. The GM scans it, picks a real name, and
materializes that entity on demand (RAG-grounded for imported books; authored
improv for original worlds) into `npcs.json` / `locations.json` — the existing
downstream loop, unchanged.

The index is *guidance, not canon prose*: a promise that a thing exists plus a
one-line seed. It grounds play in the reality of the source so the player
recognizes the figures, places, monsters, and relics of the world.

## User Stories

1. As a player, I want the GM to reach for real names from my book (Yara, the
   Tower of the Elephant, Yag-kosha) instead of inventing generic ones, so the
   world feels like the source I chose.
2. As the GM, I want a short scannable list of what exists in-context, so I can
   pick an established entity before improvising a new one.
3. As a player of an original (bookless) world, I want the same grounded roster,
   authored at world creation, so my world is equally consistent.

## Implementation Decisions

- **Schema.** `world-bible.json` gains `index` with four buckets: `npcs`,
  `locations`, `items`, `monsters`. Each entry: `{"name": ..., "note": "<one
  sentence>"}`. The old `chapters` field is removed entirely, and
  `segment_into_chapters()` is no longer used to populate the bible.
- **Named entities only.** Include the recognizable roster ("somewhat
  comprehensive"); DROP nameless typed extras ("a bold-eyed Brythunian wench").
  The index must stay small enough to sit in context every session.
- **Generation moves up a layer.** `draft_bible()` (lib) stops writing
  `chapters`. Index population is orchestrated at the command/agent layer, since
  the extractor swarm is Agent-tool subagents, not lib code. A lib/tool helper
  persists the assembled index into the bible.
- **Book path (`/import`).** Run the existing extractor agents
  (npcs/locations/items/plots + monsters) over the campaign's chunks, dedup,
  reduce each named entity to a one-sentence note, write into `index`. **Hard
  cap: 6 agents** — stated inside the subagent prompts too, because subagents
  self-fan-out. This is a NEW lighter pass, distinct from the deprecated full
  "census" extraction that `import.md` tells the GM not to run; it produces
  one-line notes for the index, not full entity records.
- **Bookless path (`/new-game`).** No RAG source exists, so the GM authors the
  index at world-creation time from the world's established tone/themes. Same
  schema, same slot.
- **Context wiring.** The scene-context assembler (`session_manager.py`) must
  emit an INDEX block from the bible so the GM actually sees it. This is net-new
  — today only `voice` is read from the bible.
- **Fallback behavior.** RAG-backed worlds expand a picked index entry by
  querying the book; invented worlds expand with authored improv. The
  downstream materialize-and-save-to-npcs.json loop is identical either way.

## Testing Decisions

- Schema/skeleton and the removal of `chapters` are assertable in code
  (`world_bible.py validate`) → agent lane.
- The INDEX block appearing in `gm-session.sh context` output is assertable →
  agent lane.
- The conan backfill (index present, no `chapters`, entries well-formed, no
  nameless junk) is assertable → agent lane.
- The `/new-game` authored-index behavior is GM prose/judgment produced by a
  command prompt — verified by a human play-through → manual lane.

## Out of Scope

- Full entity materialization (stat blocks, backstories) — the index is
  one-line seeds only; expansion into `npcs.json` is the existing play-time loop
  and unchanged.
- Resurrecting the deprecated full "census" extraction path.
- Keeping nameless typed extras as a stock/archetype cast (explicitly dropped).
- Any change to the RAG chunking/vector pipeline.

## Further Notes

- Confirmed with the user: four buckets; named-only; 6-agent hard cap; `source/`
  move of `current-document.txt` is a separate already-landed change.
- The bible IS already loaded in `session_manager.py` (line 52 / 724) — the gap
  is that only `voice` is emitted, so wiring the index in is small but real.
