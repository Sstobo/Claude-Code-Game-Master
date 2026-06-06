---
slug: story-spine-context
title: Load the story spine + "Previously on" into get_full_context
category: enhancement
kind: afk
priority: p0
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [test-harness-scaffold]
claimedBy: ss-tix001
claimedAt: 2026-06-06T03:46:41Z
changedFiles: [lib/session_manager.py, tests/test_story_spine.py]
resolution: get_full_context now assembles a story spine — PREVIOUSLY ON (last 3 session summaries), WHERE WE PAUSED cliffhanger, STORY THREADS (active plots main-first w/ latest beat), KEY FACTS (plot_local/world); count-bounded with --full override, no mid-string truncation
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T03:46:41Z
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

- [x] `get_full_context` reads and includes the last 2-3 session-log summaries.
- [x] Active/main plots from `plots.json` appear with their latest event.
- [x] Key facts (`plot_local/regional/world`) and recurring gags from `facts.json` appear.
- [x] A "WHERE WE PAUSED" cliffhanger line surfaces near the top (sources from session metadata; integrates with `session-identity-metadata` if present, else best-effort from last log entry).
- [x] `--full` flag bypasses any soft budgeting; default stays bounded but never silently truncates a single item mid-string.
- [x] New test asserts the DCC fixture context contains the main plot + last cliffhanger; PROTECT: existing pending-consequence + character blocks still present.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

### 2026-06-06T03:46:41Z — pass [ss-tix001]
`uv run pytest` → 16 passed (5 new in tests/test_story_spine.py). Evidence:
- Added a story-spine block to get_full_context (after the header, before CHARACTER) + 4 private helpers: _recent_session_summaries (parses session-log.md completed blocks), _cliffhanger (last 1-2 sentences, best-effort until session-identity-metadata lands), _active_plot_threads (active plots, main→threat→mystery→side, with latest event), _key_facts (plot_local/regional/world).
- Live `dm-session.sh context` on DCC now opens with PREVIOUSLY ON (sessions 11-13), WHERE WE PAUSED ("...847 million viewers lost their minds."), STORY THREADS ([main] The Eight Day Countdown - latest: Day 4...), and KEY FACTS (Prometheus, the Butcher, Floor 3 night danger).
- Bounded by item COUNT, never by chopping a single entry; full=True surfaces all 13 sessions.
- [human-judgement] "Recurring gags" has no dedicated facts category; the running gags (Mating Dance of Doom, Fastball Special) ride in via the loaded session summaries. A dedicated gag store can come later if wanted.
- Adversarial: every asserted substring (Session 13, Sheol Glass Reaper Case, The Eight Day Countdown, Prometheus) lives in plots.json/facts.json/session-log.md — files the pre-fix code never opened — so the tests fail against the old implementation.

## History

- 2026-06-06T03:46:41Z  in-progress → done  [ss-tix001]
- 2026-06-06T03:46:41Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
