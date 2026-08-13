---
slug: startup-active-campaign-guard
title: No more tracebacks when campaigns exist but none is active
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T18:09:55Z
changedFiles: [tools/gm-session.sh, tools/gm-enhance.sh, tools/gm-worldgen.sh, CLAUDE.md, docs/flows/play-turn.md, tests/test_active_campaign_guard.py]
resolution: loud guarded failure + campaign-selection routing when campaigns exist but none is active
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T18:43:01Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Reproduced live: campaigns on disk, `active-campaign.txt` absent →
`gm-campaign.sh list` exits 0, the GM greets the player, and the first
`gm-session.sh context` dies with a raw `RuntimeError: No active campaign`
(lib/entity_manager.py:43), because `gm-session.sh` never calls
`require_active_campaign` (tools/common.sh:98).

1. Add `require_active_campaign` to `gm-session.sh`, `gm-enhance.sh`, and
   `gm-worldgen.sh` (verify `gm-extract.sh` genuinely needs to bootstrap
   without one — if so, leave it, with a comment).
2. Ensure the guard's failure message tells the GM what to do
   ("no active campaign — run `gm-campaign.sh switch <name>` or /gm").
3. Add the missing branch to CLAUDE.md's first-time-setup tree (:10-14):
   campaigns exist but none active → route to campaign selection, not /setup.

## Acceptance criteria

- [x] With campaigns present and `active-campaign.txt` removed, `bash tools/gm-session.sh context` exits non-zero with the guard's guidance message — no Python traceback.
- [x] Same for `gm-enhance.sh` and `gm-worldgen.sh` (any state-reading verb).
- [x] CLAUDE.md's setup tree covers the "exists but none active" state with a routing destination.
- [x] `docs/flows/play-turn.md` startup section restamped if its claims moved.

## Out of scope

The full `--json` envelope work and require_active_campaign placement
consistency across all 24 wrappers (Tier 2).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T18:43:01Z — pass [review-startup]
reviewed: perfect
Notes (non-blocking): guard fires before unknown-action branch (message nit);
worldgen ""|--* branch is order-sensitive; three require_campaign copies to
consolidate into common.sh once it settles (message divergence with
require_active_campaign's "/new-game or /import first" advice) — filed as
guard-consolidation follow-up.

### 2026-08-13T18:39:59Z — verified [fable-sott1]
11/11 guard tests; live probe: gm-session.sh context with no active campaign →
exit 1, guidance message, zero tracebacks; CLAUDE.md decision tree has the
none-active branch. Implementer chose wrapper-local guards (common.sh owned by
another ticket; its require_active_campaign exits before a hint could print) —
noted for the reviewer. play-turn.md restamped after body re-read.

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-13T18:09:55Z  claimed  [fable-sott1]
- 2026-08-13T18:39:59Z  verified → in-review  [fable-sott1]
- 2026-08-13T18:43:01Z  review perfect → done, committed  [fable-sott1]
