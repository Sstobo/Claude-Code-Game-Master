---
slug: structured-trigger-schema
title: Structured consequence trigger schema (+ DCC migration)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [test-harness-scaffold]
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

Replace free-text-only triggers with a small structured schema that the engine
can evaluate, additively (old free-text triggers still parse). Each consequence
gains an optional structured trigger: `trigger_type` (on_location | on_npc |
on_time | on_event) + `match` value + optional `expiry`. Keep the existing
`consequence`/`trigger`/`created` fields. Light-migrate the DCC consequences so
the fixture exercises both structured and free-text forms.

## Acceptance criteria

- [ ] Consequence schema additively supports `trigger_type`, `match`, `expiry` (all optional; absent = legacy free-text).
- [ ] `dm-consequence.sh add` accepts structured trigger args while preserving the free-text path.
- [ ] DCC consequences migrated: at least one of each `trigger_type` present in the fixture.
- [ ] Round-trip load test: existing DCC `consequences.json` loads unchanged under the new schema (defaults applied).
- [ ] Schema documented in `docs/schema-reference.md`.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
