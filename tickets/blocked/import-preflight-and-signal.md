---
slug: import-preflight-and-signal
title: Preflight image/dep keys, kill silent-success output, fix gm-note docs drift
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
reviewRounds: null
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-14T17:56:17Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Small signal problems that each cost time during the Conan import:

1. **No preflight on OPENAI_API_KEY.** Scene images are a headline feature. The
   key's absence only surfaces at the first `gm-session.sh context`
   ("Scene images: DISABLED"), long after import, when the player is ready to
   play. Check it during import and tell the user what they're missing and how
   to enable it, while they're still in setup.
2. **Silent success.** `gm-npc.sh set-inner` prints nothing and exits 0.
   `gm-extract.sh prepare` printed nothing on failure. `gm-image.sh chronicler`
   confirms only the name, not the locked style. A tool that changed state
   should say what it changed.
3. **Docs drift.** CLAUDE.md's persistence table lists `gm-note.sh` for
   "Fact / note", but the tool requires a category argument
   (`gm-note.sh <category> <fact>`) and errors with a bare usage line. Fix the
   documented invocation.

## Acceptance criteria

- [ ] Import prints an explicit image-capability status (enabled/disabled + how to enable) before it finishes.
- [ ] `set-inner` and `chronicler` print what they persisted; `prepare` prints a diagnostic on every failure path.
- [ ] CLAUDE.md's persistence table shows the real `gm-note.sh` signature.
- [ ] No behavior change to the image pipeline itself.

## Out of scope

Adding new image features; the `set -e` bootstrap bug (bootstrap-set-e-guard);
gm-note.sh's cwd bug (persist-path-hotfixes).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
