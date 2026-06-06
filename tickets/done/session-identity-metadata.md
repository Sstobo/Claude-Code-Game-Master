---
slug: session-identity-metadata
title: Structured session footer + cliffhanger + fix session counting
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [story-spine-context]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:43:48Z
changedFiles: [lib/session_manager.py, tests/test_session_identity.py]
resolution: end_session writes a structured footer (Session/Location/Cliffhanger/Open threads); _get_session_number counts ended/started pairs (DCC=14 not ~20); _latest_session_meta surfaces cliffhanger + open threads at top of get_full_context
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:43:48Z
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

- [x] `dm-session.sh end` writes a structured footer (session N, ended_at, location, cliffhanger, open_threads).
- [x] Session number derives from matched start/end pairs; DCC reports ~13, not ~20.
- [x] Latest cliffhanger + open_threads surface at the top of `get_full_context` (feeds `story-spine-context`).
- [x] Backward-compatible read of existing `session-log.md` (no crash on legacy entries).
- [x] Test: end a session → number increments correctly → cliffhanger appears on next `get_full_context`.

## Verification

Lane: agent

## Blocked by

story-spine-context

---

## QA Reports

### 2026-06-06T04:43:48Z — pass [ss-tix001]
`uv run pytest` → 51 passed (4 new in tests/test_session_identity.py).
- end_session(summary, cliffhanger, open_threads) appends a structured footer (**Session/Location/Cliffhanger/Open threads**), human-readable + parseable. CLI `end` gains `--cliffhanger` + repeatable `--open-thread`; dm-session.sh end already passes "$@" through.
- _get_session_number now counts `### Session Ended:` + 1 if a session is open (DCC fixture → 14, well under the ~20 raw starts that caused the over-count).
- _latest_session_meta parses the most recent ended block; get_full_context prefers the structured cliffhanger (falls back to best-effort) and adds an OPEN THREADS line.
- Legacy logs without a footer still assemble (test).

## History

- 2026-06-06T04:43:48Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:43:48Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
