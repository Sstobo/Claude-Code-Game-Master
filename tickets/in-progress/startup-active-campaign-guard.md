---
slug: startup-active-campaign-guard
title: No more tracebacks when campaigns exist but none is active
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
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

- [ ] With campaigns present and `active-campaign.txt` removed, `bash tools/gm-session.sh context` exits non-zero with the guard's guidance message — no Python traceback.
- [ ] Same for `gm-enhance.sh` and `gm-worldgen.sh` (any state-reading verb).
- [ ] CLAUDE.md's setup tree covers the "exists but none active" state with a routing destination.
- [ ] `docs/flows/play-turn.md` startup section restamped if its claims moved.

## Out of scope

The full `--json` envelope work and require_active_campaign placement
consistency across all 24 wrappers (Tier 2).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
