---
slug: json-returning-wrappers
title: Bash wrappers / managers return structured JSON
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

Kill the stdout-scraping + prefix/typo bug classes without adding a process
(no MCP). Give the Python managers a structured-JSON return mode the model can
parse, and have the bash wrappers pass it through. Keep human-readable output as
default or behind a flag; add `--json` (or equivalent) so callers get typed data.
Start with the state-mutating + read wrappers the DM loop uses most.

## Acceptance criteria

- [ ] Core managers expose a `--json` output mode returning a stable, documented JSON shape (success/error envelope).
- [ ] Wrappers for player/npc/session/consequence/search support `--json` passthrough.
- [ ] Error cases return structured `{error, message}` instead of bare stderr text.
- [ ] Existing human-readable output preserved as default (no regression to interactive use).
- [ ] Tests assert JSON shape for a representative read and a representative write per manager.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
