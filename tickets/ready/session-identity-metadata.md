---
slug: session-identity-metadata
title: Structured session footer + cliffhanger + fix session counting
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [story-spine-context]
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

Close the "end on a cliffhanger, resume on the cliffhanger" loop and fix drifting
session labels. `end_session` writes a structured footer (session N, ended_at,
location, one-line cliffhanger, open_threads). Derive session number from matched
start/end pairs instead of raw "Session Started:" counts (DCC over-counts: ~20
starts for ~13 real sessions). Surface latest cliffhanger + open_threads at the
top of `get_full_context`.

## Acceptance criteria

- [ ] `dm-session.sh end` writes a structured footer (session N, ended_at, location, cliffhanger, open_threads).
- [ ] Session number derives from matched start/end pairs; DCC reports ~13, not ~20.
- [ ] Latest cliffhanger + open_threads surface at the top of `get_full_context` (feeds `story-spine-context`).
- [ ] Backward-compatible read of existing `session-log.md` (no crash on legacy entries).
- [ ] Test: end a session → number increments correctly → cliffhanger appears on next `get_full_context`.

## Verification

Lane: agent

## Blocked by

story-spine-context

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
