---
slug: scene-context-consolidation
title: Collapse dm-search / dm-enhance trio into one scene-context call
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [json-returning-wrappers]
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

The docs warn twice about getting the `dm-search` vs `dm-enhance query` vs
`dm-enhance scene` choice wrong. Collapse them into one "context for current
scene/entity" entry point that internally routes (free-text RAG vs entity lookup
vs scene context) and returns structured passages. Keep the old commands as thin
aliases or deprecate with a clear pointer. Update CLAUDE.md's Search Guide.

## Acceptance criteria

- [ ] One command returns grounded source passages for the current scene + named entities, structured JSON.
- [ ] Internal routing replaces the manual three-way choice; caller no longer needs to pick the right tool.
- [ ] Old commands still work (alias or deprecation shim) — no broken existing flows.
- [ ] CLAUDE.md Search Guide updated to the single front-door; the two "common mistake" warnings reduced/removed.
- [ ] Test: a scene-context call on the DCC fixture returns non-empty grounded passages for a known location.

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
