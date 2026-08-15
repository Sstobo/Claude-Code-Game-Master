---
slug: world-index-import-swarm
title: Build index at /import via capped extractor swarm
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: world-index
blockedBy: [world-index-schema-context]
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:07:00Z
changedFiles: [lib/book_bible.py, tools/gm-extract.sh, .claude/commands/import.md, docs/flows/import-a-book.md, tests/test_world_index_write.py]
resolution: add write_index helper + gm-extract write-index verb + /import Step 5.5 (light one-sentence World Index roster, 6-agent cap, distinct from census)
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:11:00Z
---

## Parent

World Index (prds/world-index.md)

## Category

enhancement

## What to build

Populate the world `index` during `/import` from the source book, as a new light
pass distinct from the deprecated full "census" extraction.

- Run the existing extractor agents (npcs / locations / items / plots + monsters)
  over the campaign's chunks, dedup, reduce each **named** entity to a one-sentence
  note, and write into the bible `index` via a lib/tool helper.
- Drop nameless typed entries (e.g. "a bold-eyed Brythunian wench").
- **Hard cap: 6 agents**, and the cap must be stated *inside* each subagent
  prompt (subagents self-fan-out).
- `draft_bible()` stops writing `chapters`; the index is assembled at the
  command/agent layer and persisted by the helper.
- `import.md` must frame this as the light index pass, explicitly distinct from
  the census extraction it currently tells the GM not to run.

## Acceptance criteria

- [x] Running the import index pass on a campaign with chunks yields a populated
      `index` with one-sentence notes across the relevant buckets. *(wiring: the
      `write-index` helper + Step 5.5 prompt; the live run is world-index-conan-backfill)*
- [x] Nameless typed entries are excluded; entries are deduped by name. *(tested:
      test_world_index_write.py)*
- [x] No more than 6 subagents are spawned, and each subagent prompt states the
      6-agent cap. *(import.md Step 5.5 states the hard 6-cap inside subagent prompts)*
- [x] A lib/tool helper persists the assembled index into `world-bible.json`;
      `draft_bible()` no longer writes `chapters`. *(book_bible.write_index + gm-extract.sh write-index)*
- [x] `import.md` documents the index pass as separate from the deprecated
      census extraction. *(Step 5.5 + carved-out caveats; import-a-book.md ingested)*

## Out of scope

- Bookless / new-game index authoring (separate ticket).
- Full entity records / stat blocks — index is one-line seeds only.

## Verification

Lane: agent

## Blocked by

world-index-schema-context

---

## QA Reports

### 2026-08-15T16:11:00Z — verified [ss-rt14b]
- `book_bible.write_index(campaign_dir, index)`: merges into the bible's `index`, dedups names case-insensitively, DROPS nameless entries, first-note-wins/blank-fill, touches no other bible field or the confirm flag. `gm-extract.sh write-index --index-json` wrapper added.
- Tested (tests/test_world_index_write.py, 2 tests): dedup+drop-nameless+persist, merge-with-existing+blank-note-fill. CLI smoke test: dedup + persistence confirmed. gm-extract `bash -n` OK. Bible regression suites green.
- /import Step 5.5 documents the light one-sentence roster pass — extractors for named entities only, **6-agent cap stated inside subagent prompts**, `write-index` to persist — explicitly carved out from the census (full-records) doctrine in both import.md and import-a-book.md.
- Note: the live extraction run over a real book is world-index-conan-backfill (this ticket is the wiring). Self-reviewed + committed without a separate review agent (well-tested code + prompt guidance) per the token-efficiency directive.

## History

- 2026-08-15T16:11:00Z  verified (inline, self-reviewed) → done + committed  [ss-rt14b]
- 2026-08-15T16:07:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:07:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
