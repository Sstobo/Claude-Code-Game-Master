---
slug: world-bible-schema
title: Define world-bible.json (voice/factions/themes/geography/systems)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [world-kit-schema]
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

The structured fidelity spine for a world. Define `world-bible.json`: VOICE
(prose style, rhythm, signature vocab, sample passages), TONE, THEMES, FACTIONS
as a graph (allegiances/conflicts/territory), GEOGRAPHY as a place-graph with
real adjacency, TIMELINE, and the book's SIGNATURE SYSTEMS. This is what
auto-drafts the bespoke ruleset + `campaign_rules`. Hand-author one for DCC first
to validate the schema (DCC's `campaign_rules` was hand-written — codify what
made it good).

## Acceptance criteria

- [ ] `world-bible.json` schema defined + documented (voice, tone, themes, factions-graph, geography-graph, timeline, signature systems).
- [ ] A hand-authored DCC `world-bible.json` validates against the schema.
- [ ] Schema maps cleanly onto `ruleset.json` + `campaign_rules` (the auto-draft target in the next ticket).
- [ ] Loadable as the canonical spine at session start (read path defined).
- [ ] Test: DCC world-bible loads + the factions/geography graphs parse.

## Verification

Lane: agent

## Blocked by

world-kit-schema

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
