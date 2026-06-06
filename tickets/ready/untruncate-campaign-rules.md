---
slug: untruncate-campaign-rules
title: Stop truncating campaign_rules in session context
category: enhancement
kind: afk
priority: p0
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [test-harness-scaffold]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Highest-ROI fix in the roadmap. `get_full_context` truncates every
`campaign_rules` value to 220 chars (near `session_manager.py:468`), so the DM is
told "follow your world's rules exactly" while shown only half of them
(`dm_checklist`, `achievement_checks`, `opening_ceremony`, `reaction_types` are
cut). Render the full `campaign_rules` as a distinct, clearly-labeled
"YOUR WORLD'S RULES — follow exactly" block with NO truncation. Soft token
target is guidance only; never a silent cutoff.

## Acceptance criteria

- [ ] `campaign_rules` values are emitted in full (no 220-char cut) in `get_full_context`.
- [ ] Rules render as their own labeled block, visually separate from the NPC/consequence summaries.
- [ ] Running `bash tools/dm-session.sh context` on DCC shows the full `loot_box_system`, `audience_system`, `interview_system` text with no trailing `...`.
- [ ] Optional token count of the context block is logged/observable (no enforced ceiling).
- [ ] Characterization snapshot from `test-harness-scaffold` updated intentionally; new test asserts a known full-rule substring is present.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
