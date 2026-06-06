---
slug: story-spine-context
title: Load the story spine + "Previously on" into get_full_context
category: enhancement
kind: afk
priority: p0
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

Fix the #1 continuity failure. Today `get_full_context` never reads
`plots.json`, `facts.json`, or `session-log.md` — the DM starts each session
knowing party HP but not the main plot or last cliffhanger. Assemble a true
narrative-aware turn-0 block: last 2-3 session-log summaries verbatim, a
"WHERE WE PAUSED" cliffhanger line, active/main plots with their latest event,
and `plot_local/regional/world` facts + recurring gags. Token-budgeted (~1.5-2k
as guidance, never a hard cut) with a `--full` override.

## Acceptance criteria

- [ ] `get_full_context` reads and includes the last 2-3 session-log summaries.
- [ ] Active/main plots from `plots.json` appear with their latest event.
- [ ] Key facts (`plot_local/regional/world`) and recurring gags from `facts.json` appear.
- [ ] A "WHERE WE PAUSED" cliffhanger line surfaces near the top (sources from session metadata; integrates with `session-identity-metadata` if present, else best-effort from last log entry).
- [ ] `--full` flag bypasses any soft budgeting; default stays bounded but never silently truncates a single item mid-string.
- [ ] New test asserts the DCC fixture context contains the main plot + last cliffhanger; PROTECT: existing pending-consequence + character blocks still present.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
