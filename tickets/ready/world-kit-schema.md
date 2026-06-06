---
slug: world-kit-schema
title: World Kit — ruleset.json + campaign-scoped rules Skill loader
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [generic-core]
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

The per-book ruleset layer on top of the generic core. Define `ruleset.json`
(stat schema, progression model, resolution model, active specialist agents) and
a campaign-scoped rules **Skill** holding that world's mechanics/prose, loaded on
demand. `campaign_rules` stays for world-flavor systems (loot boxes, viewers).
Ship the DCC ruleset as the first real kit (resource-axis: viewers + floor
descent), proving the core + kit split end-to-end. PROTECT the `campaign_rules`
engine.

## Acceptance criteria

- [ ] `ruleset.json` schema defined + documented (stat schema, progression model, resolution model, active agents).
- [ ] A campaign's rules Skill loads on demand and drives play through the generic core.
- [ ] DCC ships as a working kit (resource-axis progression) without a 5e XP track.
- [ ] `campaign_rules` (loot boxes, audience, interview systems) preserved and consumed by the kit.
- [ ] Test: DCC kit resolves a check + advances progression via its declared model, not 5e leveling.

## Verification

Lane: agent

## Blocked by

generic-core

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
