---
slug: json-wrappers-session
title: --json mode for session_manager (context/status read + move write)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [json-returning-wrappers]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:49:00Z
changedFiles: [lib/session_manager.py, tools/dm-session.sh, tests/test_json_wrappers_session.py]
resolution: session_manager --json envelopes status/context (read) and move (write) via cli_output; dm-session.sh forwards --json; human output unchanged
createdAt: 2026-06-06T04:10:42Z
updatedAt: 2026-06-06T04:49:00Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Wire the shared `cli_output` envelope into session_manager. Add `--json` to its
CLI for a representative read (`status` and/or `context`) and a representative
write (`move`), returning `{"ok", "data"|"error"}`. Preserve human-readable
output as default.

## Acceptance criteria

- [x] `session_manager.py status --json` and `context --json` emit the success envelope.
- [x] `move --json` emits a structured success/error envelope.
- [x] Human output unchanged without `--json`.
- [x] `dm-session.sh` passes `--json` through.
- [x] Tests assert envelope shape for the read and the write (hermetic, DCC fixture).

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

### 2026-06-06T04:49:00Z — pass [ss-tix001]
`uv run pytest` → 57 passed (2 new). main() detects wants_json()/strip_json_flag and envelopes status (read), context (read), move (write) before normal dispatch; other actions + human output unchanged. dm-session.sh status/move/context forward "$@". Live: `python lib/session_manager.py status --json` → `{"ok": true, "data": {...}}`. Hermetic tests envelope get_status + move_party through emit.

## History

- 2026-06-06T04:49:00Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:49:00Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T04:10:42Z  created → ready  [ss-tix001]
