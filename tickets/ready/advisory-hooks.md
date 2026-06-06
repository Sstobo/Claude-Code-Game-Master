---
slug: advisory-hooks
title: Advisory persist-before-narrate hook + Stop auto-save
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

Make the product's #1 invariant mechanical, not prose-dependent. There are
currently zero hooks (`.claude/settings.json` has statusLine only). Add a
`PostToolUse` hook that validates/logs state-writing tool calls, and a `Stop`
hook that auto-saves/ends the session so progress is never lost. Non-blocking and
advisory — warn, log, auto-correct; do not hard-block a narration turn.

## Acceptance criteria

- [ ] `.claude/settings.json` gains a `PostToolUse` hook that logs/validates state writes (no hard block).
- [ ] A `Stop` hook auto-runs session save so a player never loses progress.
- [ ] Advisory warning emitted when a turn changed HP/gold/location with no corresponding persist call (best-effort).
- [ ] Hooks are non-blocking; a failing hook never wedges the session.
- [ ] Documented in CLAUDE.md (how enforcement now works) + statusLine config preserved.

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
