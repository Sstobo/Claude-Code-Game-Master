---
slug: wrapper-cwd-anchoring
title: Every tools/ wrapper resolves world-state against the caller's cwd
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T14:01:47Z
changedFiles: [tools/common.sh, tools/gm-note.sh, tools/gm-time.sh, tools/gm-extract.sh, docs/conventions/tool-wrapper-contract.md, tests/test_wrapper_cwd_anchoring.py]
resolution: one cd in common.sh makes every wrapper cwd-safe; CALLER_PWD preserves relative path args
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T20:42:00Z
updatedAt: 2026-08-14T14:47:08Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Found by persist-path-hotfixes: CampaignManager/EntityManager default to the
relative string "world-state", so every wrapper that doesn't `cd` to the repo
root resolves campaign state against the CALLER'S cwd. Proven:
`cd /tmp && bash <repo>/tools/gm-player.sh show` fails with "No active
campaign" and silently creates `/tmp/world-state/campaigns/`. Subagents get
cwd resets between Bash calls, so this is a live corruption/confusion vector
(state written to stray world-state trees, then "lost"). gm-note.sh and
gm-time.sh were fixed by adding `cd "$PROJECT_ROOT" || exit 1` after the
campaign guard; every other wrapper still has the latent bug. `uv run` from a
foreign cwd also resolves to a depless ephemeral env — the cd fixes that too.

Fix in ONE place: add the `cd "$PROJECT_ROOT" || exit 1` to tools/common.sh
(after PROJECT_ROOT is derived, before campaign resolution) so all 25 wrappers
inherit it, and remove the now-redundant per-wrapper cds in gm-note.sh /
gm-time.sh. Audit wrappers that intentionally consume the caller's cwd for
relative file arguments (gm-extract.sh prepare takes a PDF path; gm-image.sh
outputs) — resolve such args to absolute paths BEFORE the cd, or capture
`CALLER_PWD` in common.sh for them.

## Acceptance criteria

- [x] A parametrized test runs a representative read verb of every wrapper from a foreign cwd: exit status matches repo-root behavior and NO stray world-state/ is created in the foreign cwd.
- [x] File-path arguments still work relative to the caller's cwd (test gm-extract.sh prepare with a relative PDF path from a foreign cwd, or document the absolute-path requirement in its usage).
- [x] gm-note.sh / gm-time.sh keep passing their foreign-cwd tests with the per-wrapper cd removed.
- [x] Full suite passes.

## Out of scope

The --json envelope work; python-side default-path refactors (the cd makes the
relative default safe).

## Verification

Lane: agent

## Blocked by

None (land after the in-review wave commits to avoid tool-file overlap).

---

## QA Reports

### 2026-08-14T14:47:08Z — pass [review-cwd]
reviewed: perfect (reviewer independently rebuilt a no-cd tree and proved
the decoy test binds). Nits: gm-extract source claim added pre-commit;
docstring says ~25 wrappers vs 14 swept (mechanism is one shared line);
deliberate test overlap noted; python-side relative default remains for
DIRECT python calls only — contract already forbids those; recorded.

### 2026-08-14T14:42:18Z — verified [fable-sott1]
Decoy-world-state test proven to bind (fails with the cd disabled while the
pinned sweep passes — the implementer caught that the planned test was
decorative); 14-wrapper no-litter sweep; gm-extract prepare resolves
relative docs via CALLER_PWD (only path-arg wrapper, verified by grep);
gm-image needs nothing. Implementer full suite 543 passed.

## History

- 2026-08-13T20:42:00Z  created → ready (from persist-path-hotfixes finding)  [fable-sott1]
- 2026-08-14T14:01:47Z  claimed  [fable-sott1]
- 2026-08-14T14:34:23Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T14:42:18Z  verified → in-review  [fable-sott1]
- 2026-08-14T14:47:08Z  review perfect → done, committed  [fable-sott1]
