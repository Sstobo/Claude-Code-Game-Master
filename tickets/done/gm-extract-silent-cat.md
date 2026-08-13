---
slug: gm-extract-silent-cat
title: gm-extract.sh raw active-campaign cat sites die silently under set -e
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: [import-extraction-repair, extraction-output-verification]
claimedBy: fable-sott1
claimedAt: 2026-08-13T19:23:43Z
changedFiles: [tools/gm-extract.sh, lib/campaign_manager.py, tests/test_bootstrap_no_campaign.py, docs/flows/import-a-book.md]
resolution: extract verbs fail loudly, resolve legacy dirs, and cannot be traversed out of campaigns/
reviewRounds: 3
implementer: null
createdAt: 2026-08-13T18:10:00Z
updatedAt: 2026-08-13T21:38:24Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Found by bootstrap-set-e-guard's audit: gm-extract.sh open-codes the
active-campaign read as `campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt"
2>/dev/null)` at ~13 sites (lines 267, 340, 412, 483, 520, 535, 550, 565, 580,
595, 610, 625, 640 pre-wave-1). `2>/dev/null` hides the message but not the
exit status; with no campaign file, `cat` returns 1 and `set -e` kills the
script with zero output. Measured: `validate`, `archive`, `normalize`, `cap`,
`spine` each exit 1 silently when no campaign is active — the identical
silent-death signature bootstrap-set-e-guard fixed in common.sh, from a second
cause.

Fix: replace every raw `cat` with common.sh's `get_active_campaign` (always
exits 0); where an empty result is fatal for the verb, fail loudly with a
diagnostic. Extend tests/test_bootstrap_no_campaign.py's parametrized
no-silent-death test to cover `gm-extract.sh validate`, `normalize`, `cap`,
`spine`, `archive`.

Blocked until the two in-flight gm-extract.sh tickets land (file ownership).
Line numbers above will have shifted — re-grep, don't trust them.

## Acceptance criteria

- [x] No `$(cat "$WORLD_STATE_BASE/active-campaign.txt" ...)` remains in gm-extract.sh (grep-verifiable).
- [x] With no active campaign, every gm-extract.sh verb either succeeds (bootstrap verbs) or exits non-zero WITH a printed diagnostic — never silently.
- [x] The no-silent-death parametrized test covers the five verbs listed above.
- [x] Full suite passes.
- [x] (review) campaign_dir fails on non-zero rc even with junk stdout.
- [x] (review) clean on a nonexistent campaign is idempotent (exit 0 with notice).
- [x] (review-2) resolve rejects any name not resolving to a direct child of campaigns/; clean "../x" cannot escape.

## Out of scope

The validate/normalize gate semantics (extraction-output-verification owns
those); common.sh (already fixed).

## Verification

Lane: agent

## Blocked by

import-extraction-repair, extraction-output-verification

---

## QA Reports

### 2026-08-13T21:38:24Z — pass [review-silentcat-3]
reviewed: perfect (round 3; traversal closed at three layers, symlink case
held by the realpath guard). Nits: macOS case-verbatim resolution (already
ticketed as campaign-path-exact-match) and a cosmetic trailing-slash echo.
Three rounds, three real catches: junk-stdout path, clean idempotency,
path traversal into rm -rf.

### 2026-08-13T21:15:10Z — fail [review-silentcat-2]
reviewed: needs-changes (round 2). Path traversal: _resolve_in's first
branch returns a '..'-bearing name verbatim; clean '../rag' deleted
world-state/rag in an isolated tree (exit 0). Pre-change impossible because
_slugify stripped '/' and '.'. Criteria 1-2 from round 1 confirmed holding.

### 2026-08-13T21:13:01Z — verified (fix round 1) [fable-sott1]
rc-3/rc-1 split gives clean idempotency without weakening loud failure;
junk-stdout stub test proves the rc guard protects against bogus paths.
Implementer full suite 393 passed; clean-missing exits 0 verified live.

### 2026-08-13T20:47:45Z — fail [review-silentcat]
reviewed: needs-changes (both low; all acceptance criteria hold)
1. campaign_dir judges success by non-empty stdout only — junk stdout from a
failing interpreter would yield rc 0 and a bogus path that clean rm -rfs.
Guard on rc too.
2. clean <nonexistent> regressed from idempotent exit-0 notice to exit 1.

### 2026-08-13T20:38:00Z — verified [fable-sott1]
Zero raw-cat sites (grep 0); live probe pre-fix showed validate/normalize/
cap/spine/archive dying silently, post-fix all verbs fail loudly or
bootstrap; legacy underscore dir reachable via new resolve verb (test-
pinned); no_active_campaign fixture now uses atomic os.replace sidecar.
import-a-book.md slug bullet updated + restamped. Implementer suite green
(372 excl. reset file mid-flight; reset file 19/19 after state fix).

## History

- 2026-08-13T18:10:00Z  created → ready (from bootstrap-set-e-guard audit)  [fable-sott1]

## Triage note (2026-08-13, fable-sott1, from whole-branch review)

Related resolution gap in the same file: campaign_slug() re-slugifies instead
of resolving, so a legacy folder like curse_of_strahd (underscores) written to
active-campaign.txt by gm-campaign.sh switch is unreachable from every
gm-extract verb ("Campaign directory not found: .../curse-of-strahd").
Fix together with the raw-cat sweep: add a `resolve` verb to
campaign_manager's CLI routing through _resolve_name, and have gm-extract.sh
use it wherever it needs a directory (slugify stays for NEW names only).
- 2026-08-13T19:23:43Z  claimed  [fable-sott1]
- 2026-08-13T20:27:26Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T20:38:00Z  verified → in-review  [fable-sott1]
- 2026-08-13T20:47:45Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T21:13:01Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T21:15:10Z  review needs-changes (round 2) — final fix cycle  [fable-sott1]
- 2026-08-13T21:38:24Z  review perfect → done, committed  [fable-sott1]
