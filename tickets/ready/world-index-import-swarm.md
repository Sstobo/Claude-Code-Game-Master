---
slug: world-index-import-swarm
title: Build index at /import via capped extractor swarm
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: world-index
blockedBy: [world-index-schema-context]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
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

- [ ] Running the import index pass on a campaign with chunks yields a populated
      `index` with one-sentence notes across the relevant buckets.
- [ ] Nameless typed entries are excluded; entries are deduped by name.
- [ ] No more than 6 subagents are spawned, and each subagent prompt states the
      6-agent cap.
- [ ] A lib/tool helper persists the assembled index into `world-bible.json`;
      `draft_bible()` no longer writes `chapters`.
- [ ] `import.md` documents the index pass as separate from the deprecated
      census extraction.

## Out of scope

- Bookless / new-game index authoring (separate ticket).
- Full entity records / stat blocks — index is one-line seeds only.

## Verification

Lane: agent

## Blocked by

world-index-schema-context

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
