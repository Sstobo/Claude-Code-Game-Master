---
slug: play-pack
title: Play pack — kit, primer, one room; the book stays the book
status: active
version: 1
supersedes: trust-the-agent
createdAt: 2026-08-15T11:46:00Z
updatedAt: 2026-08-15T11:46:00Z
---

## Problem Statement

Setup was building a second copy of the book (extractors, fan-out, gazetteers)
before anyone sat down. Players came to talk to someone in a book they brought.
They got a loading screen.

## Solution

Any book the user supplies is the world. Index it once. Setup writes only a
**play pack**: kit, voice, a GM primer, one starting room. RAG pulls authentic
author language and lore during play. The campaign JSON is a journal of where
the table has been.

1. A `play_pack` object on the overview, surfaced every beat.
2. `/import` writes that pack + a stage — never the four extractors.
3. `/new-game` writes kit + primer + one street — fan-out is not the default.
4. One verb materializes a single name from the book when play walks toward it.

## User Stories

1. As a player, I drop in any PDF and step into *that* author's world tonight,
   not after a census.
2. As the GM, I get a primer (whose story, this room, who is here, the hook,
   what is offstage) and the book on my chair via RAG.
3. As a player, when I walk somewhere new, that place is read from the book
   and written into the journal — not pre-filed.

## Implementation Decisions

- `play_pack` lives on `campaign-overview.json` (no new state file).
- Context renders a PRIMER block when any pack field is set.
- `lib/play_pack.py` + `tools/gm-playpack.sh` own set / stage / from-book.
- RAG is the live text. Extraction is not a substitute.
- Default `rag_inspiration` on — the book is how the table sounds.

## Testing Decisions

- Pack in overview → context contains PRIMER and the hook; no fake session.
- `stage` writes 1 location + present NPCs + exits; does not invent a gazetteer.
- `from-book` with an explicit description persists exactly one entity.
- Agent-lane.

## Out of Scope

Extractor quality, reconciler, fan-out caps, import-preflight, rebuilding Conan.

## Further Notes

Sliced after the holodeck/1983-table rewrite. `trust-the-agent` is superseded —
its shipped work stands; this is the next product cut.
