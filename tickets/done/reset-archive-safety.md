---
slug: reset-archive-safety
title: Make gm-reset archive real and destructive commands non-interactive-safe
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T16:06:15Z
changedFiles: [tools/gm-reset.sh, tools/gm-campaign.sh, tests/test_reset_archive.py, .gitignore, .claude/commands/reset.md]
resolution: archive is a real directory copy with guarded failure; destructive commands non-interactive-safe with --yes
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T18:38:34Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

`gm-reset.sh archive` advertises a git-branch backup, but `.gitignore:23`
excludes `world-state/campaigns/*`, so the branch captures nothing (failures
swallowed by `|| true`, tools/gm-reset.sh:152-157) and the reset then deletes
for real. It also creates `archive/*` branches against the trunk-only
workflow, and both `gm-reset.sh` (:166,190) and `gm-campaign.sh` (:75) block
on interactive `read -p` with no non-interactive path.

1. Replace the git-branch archive with a plain directory copy:
   `world-state/archive/<campaign>-<timestamp>/` (cp -R or tar). No branches.
   Fix the printed recovery instructions to match.
2. Remove the unguarded `git commit` at gm-reset.sh:172-173 (or make the whole
   git interaction go away with the branch approach).
3. Add `--yes` (accept `--confirm`) to `gm-reset.sh` and
   `gm-campaign.sh delete`, and gate every `read -p` on `[ -t 0 ]` — in a
   non-tty without `--yes`, abort with a clear message instead of hanging.

## Acceptance criteria

- [x] A test (or scripted check) archives a fixture campaign, resets, and restores it byte-identical from `world-state/archive/`.
- [x] `gm-reset.sh` creates no git branches and never runs `git commit` on an empty index.
- [x] `gm-reset.sh --yes` and `gm-campaign.sh delete <name> --yes` complete without a tty; without `--yes` in a non-tty they exit non-zero with a clear message.
- [x] Recovery instructions printed by the tool reference the real archive location.

## Out of scope

`gm-reset.sh hard` semantics, campaign migration tooling, the broader --json
contract work (Tier 2).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T18:38:34Z — pass [review-reset-2]
reviewed: perfect (followup round; all five focused criteria hold)

### 2026-08-13T18:34:38Z — verified (fix round 1) [fable-sott1]
10/10 reset tests pass; zero git checkout/branch references in reset.md and
gm-reset.sh; both documented invocations pass --yes; copy/mkdir guarded with
abort-before-reset; delete rejects flag-shaped names. Implementer full suite
292 passed.

### 2026-08-13T18:31:34Z — fail [review-reset]
reviewed: needs-changes
1. .claude/commands/reset.md:36,47,84-89 — /reset invokes gm-reset.sh without --yes; under the new tty gate the documented flow always exits 1 (GM runs via Bash, no tty). Chat confirm already happened at STEP 1 → pass --yes.
2. .claude/commands/reset.md:23,40-43,76-79 — still documents the git-branch archive and `git checkout ... -- world-state/` restore, which now restores nothing.
3. tools/gm-reset.sh:178-183 — cp -R unguarded, no set -e: a failed/partial copy falls through to reset_world (data loss in a new shape). Guard with `|| exit 1`.
Nits (non-blocking): require_confirmable inverted return convention + duplicated tty gate; `delete --yes` with no name mis-parses --yes as the campaign name.

### 2026-08-13T18:08:37Z — verified [fable-sott1]
7/7 new tests pass; full suite 278 passed. Non-tty archive and campaign-delete
exit 1 with guidance; --yes paths complete; no git operations remain in
gm-reset.sh; round-trip byte-identical per test. Orchestrator added
world-state/archive/ to .gitignore (implementer flagged, out of its scope).

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-13T16:06:15Z  claimed  [fable-sott1]
- 2026-08-13T18:04:14Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T18:08:37Z  verified → in-review  [fable-sott1]
- 2026-08-13T18:31:34Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T18:34:38Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T18:38:34Z  review perfect → done, committed  [fable-sott1]
