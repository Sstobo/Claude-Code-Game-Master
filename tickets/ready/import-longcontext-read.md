---
slug: import-longcontext-read
title: Long-context import — keep the book, generate the world-bible
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [world-bible-schema]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Replace chunk-and-embed-then-delete with long-context reading. Stop deleting the
book text on cleanup (`agent_extractor.py:~629`); keep chapter-segmented text. On
import, a world-bible subagent reads large spans (whole chapters via long
context, not 3000-char chunks) and emits one `world-bible.json` per world, which
auto-drafts the bespoke ruleset + `campaign_rules`. Keep the existing four-bucket
NPC/location/item/plot extraction (PROTECT canonical-voice extraction).

## Acceptance criteria

- [ ] Book text is retained (chapter-segmented), not deleted on import cleanup.
- [ ] A world-bible subagent reads large spans and produces a valid `world-bible.json`.
- [ ] The bible auto-drafts a `ruleset.json` + `campaign_rules` for the imported world.
- [ ] Existing entity extraction (NPCs/locations/items/plots + verbatim voice) still runs and is preserved.
- [ ] Token usage of the import is logged/observable (no silent cap).
- [ ] Test/dry-run on a small public-domain text (e.g. a Conan/Belit excerpt) produces a parseable bible.

## Verification

Lane: agent

## Blocked by

world-bible-schema

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
