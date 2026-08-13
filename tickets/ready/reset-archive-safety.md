---
slug: reset-archive-safety
title: Make gm-reset archive real and destructive commands non-interactive-safe
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

- [ ] A test (or scripted check) archives a fixture campaign, resets, and restores it byte-identical from `world-state/archive/`.
- [ ] `gm-reset.sh` creates no git branches and never runs `git commit` on an empty index.
- [ ] `gm-reset.sh --yes` and `gm-campaign.sh delete <name> --yes` complete without a tty; without `--yes` in a non-tty they exit non-zero with a clear message.
- [ ] Recovery instructions printed by the tool reference the real archive location.

## Out of scope

`gm-reset.sh hard` semantics, campaign migration tooling, the broader --json
contract work (Tier 2).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
