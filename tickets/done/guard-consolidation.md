---
slug: guard-consolidation
title: One campaign-guard implementation; unified message; unknown-action ordering
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T14:50:33Z
changedFiles: [tools/common.sh, tools/gm-session.sh, tools/gm-enhance.sh, tools/gm-worldgen.sh, tests/test_active_campaign_guard.py, docs/conventions/tool-wrapper-contract.md]
resolution: one campaign guard, actionable everywhere; typos report as typos; the escape hatch names itself
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T18:45:00Z
updatedAt: 2026-08-14T15:43:25Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

enhancement

## What to build

Post-wave-1 cleanup from review-startup (all non-blocking notes):

1. Three identical wrapper-local `require_campaign()` copies live in
   gm-session.sh, gm-enhance.sh, gm-worldgen.sh (written while common.sh was
   owned by another ticket, now landed). Consolidate into common.sh —
   either upgrade `require_active_campaign`'s message (it still says "Run
   /new-game or /import first", which CLAUDE.md's decision tree now calls
   wrong for the campaigns-exist state) or have it print the list/switch
   guidance; delete the three copies. `grep -c require_campaign tools/*.sh`
   ends at 0.
2. Guard ordering: gm-session.sh fires the guard before the `*)` unknown-
   action branch, so a typo'd verb reports "No active campaign" instead of
   "Unknown action"; `--help` also hits the guard. Route help/unknown-action
   before the guard (match gm-enhance.sh's help exemption).
3. gm-worldgen.sh `""|--*` name detection is order-sensitive
   (`consolidate --json my-world` guards despite a name) — parse the name
   positionally regardless of flag order or document flag-last.
4. Pin the bootstrap escape hatch: a test asserting
   `gm-worldgen.sh consolidate <campaign>` reaches world_author with
   active-campaign.txt absent.

## Acceptance criteria

- [x] One guard implementation repo-wide, message includes the list/switch guidance.
- [x] `gm-session.sh --help` and `gm-session.sh typo` (no campaign) print usage / unknown-action respectively.
- [x] Explicit-name worldgen verbs run pre-activation regardless of flag order (test-pinned).
- [x] Full suite passes.

## Out of scope

New guard coverage for other tools; --json envelope work.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T15:43:25Z — pass [review-guard-2]
reviewed: perfect (round 2; subshell exit semantics and glob safety proven
by execution). Nits: reverse-set assertion suggestion recorded; the ONLY-
guard doc claim gained the resolver-exemption clause pre-commit (restamped).

### 2026-08-14T15:40:50Z — verified (fix round 1) [fable-sott1]
Escape-hatch hint as a fourth aligned repair line (deviation accepted —
better than the brief); VALID_ACTIONS single source with a glob-safe
membership loop; both new pins pass. Orchestrator folded the held contract-
doc sentence (doc now free) and restamped after re-reading the body.
Implementer full suite 554 passed.

### 2026-08-14T15:26:15Z — fail [review-guard]
reviewed: needs-changes (both minor)
1. Worldgen's escape hatch lost its discoverability — the old 'Name one explicitly' hint was dropped in unification.
2. gm-session's Unknown-action echo lists 11 verbs, three lines from the guard's 14 — lists disagree in plain sight; verb list duplicated in three places.
Verified: all 14 verbs guarded, resolver deviation sound, no stale-text test breakage.

### 2026-08-14T15:22:26Z — verified [fable-sott1]
Guard tests green; live probes: typo reports itself, --help exits 0, named
worldgen verbs skip the guard in any flag order. Deviation accepted:
gm-extract's require_campaign is a resolver, not a guard copy — grep test
asserts it is the sole remainder. Contract-doc sentence held for fold at
commit (sibling ticket owns the doc right now). Implementer suite 551 passed.

## History

- 2026-08-13T18:45:00Z  created → ready (from review-startup notes)  [fable-sott1]
- 2026-08-14T14:50:33Z  claimed  [fable-sott1]
- 2026-08-14T14:54:08Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T15:22:26Z  verified → in-review  [fable-sott1]
- 2026-08-14T15:26:15Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-14T15:40:50Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-14T15:43:25Z  review perfect → done, committed  [fable-sott1]
